"""
UnblockCord — Background Daemon Thread
Periyodik olarak Discord IP'lerini güncelleyen arka plan iş parçacığı.
PyQt6 sinyalleri aracılığıyla UI ile iletişim kurar.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

from PyQt6.QtCore import QThread, pyqtSignal

from app.config import DOMAINS, INTERVALS, DEFAULT_INTERVAL
from app.core.dns_resolver import resolve_all
from app.core.hosts_manager import (
    update_hosts,
    backup_hosts,
    has_existing_backup,
    HostsManagerError,
)
from app.core.connectivity import check_discord_connectivity, flush_dns_cache
from app.core.discord_manager import restart_discord, is_discord_running
from app.core.sni_proxy import get_proxy


# ---------------------------------------------------------------------------
# Veri sınıfı
# ---------------------------------------------------------------------------

@dataclass
class UpdateResult:
    """Tek bir güncelleme döngüsünün sonucunu taşır."""
    success:   bool
    ip_map:    dict
    connected: bool
    latency:   float
    message:   str
    timestamp: datetime = field(default_factory=datetime.now)


# ---------------------------------------------------------------------------
# Daemon thread
# ---------------------------------------------------------------------------

class DaemonThread(QThread):
    """
    Arka plan güncelleme döngüsü:
      1. Cloudflare DoH'dan IP çek
      2. Hosts dosyasını güncelle
      3. DNS önbelleğini temizle
      4. Discord'a bağlantı testi yap
    Her adım için UI'ya sinyal gönderilir.
    """

    # Sinyaller
    update_started   = pyqtSignal()
    update_finished  = pyqtSignal(object)      # UpdateResult
    log_message      = pyqtSignal(str, str)    # (mesaj, seviye)
    countdown_tick   = pyqtSignal(int)         # kalan saniye

    def __init__(self, parent=None):
        super().__init__(parent)
        self._interval_hours: float = INTERVALS.get(DEFAULT_INTERVAL, 6)
        self._running              = False
        self._force_update         = False
        self._auto_restart_discord = False
        self._next_update: Optional[datetime] = None

    def set_auto_restart_discord(self, enabled: bool) -> None:
        """Güncelleme sonrası Discord'u otomatik yeniden başlat."""
        self._auto_restart_discord = enabled

    # ------------------------------------------------------------------
    # Dış arayüz
    # ------------------------------------------------------------------

    def set_interval(self, interval_name: str) -> None:
        """Güncelleme aralığını güncelle (görüntü adından)."""
        self._interval_hours = INTERVALS.get(interval_name, 6)
        if self._next_update:
            self._next_update = datetime.now() + timedelta(hours=self._interval_hours)

    def trigger_update(self) -> None:
        """Bir sonraki tick'te zorla güncelleme yap."""
        self._force_update = True

    def stop(self) -> None:
        """Thread'i nazikçe durdur."""
        self._running = False
        self.wait(5000)

    # ------------------------------------------------------------------
    # Ana döngü
    # ------------------------------------------------------------------

    def run(self) -> None:
        self._running     = True
        self._next_update = datetime.now()          # Hemen guncelle

        # SNI bypass proxy'yi baslat (updates.discord.com icin)
        proxy = get_proxy()
        if not proxy.is_running():
            proxy.start(log_cb=lambda m, l: self.log_message.emit(m, l))

        while self._running:
            now = datetime.now()

            if self._force_update or now >= self._next_update:
                self._force_update = False
                self._do_update()
                self._next_update = datetime.now() + timedelta(hours=self._interval_hours)

            # Geri sayim sinyali
            if self._next_update:
                remaining = max(0, int((self._next_update - datetime.now()).total_seconds()))
                self.countdown_tick.emit(remaining)

            self.msleep(1000)

        proxy.stop(log_cb=lambda m, l: self.log_message.emit(m, l))

    # ------------------------------------------------------------------
    # Güncelleme döngüsü
    # ------------------------------------------------------------------

    def _do_update(self) -> None:
        self.update_started.emit()
        self.log_message.emit("━━━ Güncelleme başlatıldı ━━━", "info")

        try:
            # 1) İlk çalıştırmada yedek al
            if not has_existing_backup():
                backup_path = backup_hosts()
                self.log_message.emit(
                    f"Hosts yedeklendi → {backup_path.name}", "info"
                )

            # 2) IP cözümleme  (Cloudflare DoH → Google DoH → nslookup fallback)
            self.log_message.emit(
                "Discord IP adresleri cözümlüyor...", "info"
            )
            raw = resolve_all(DOMAINS)   # {domain: (ip|None, err|None)}

            # Sadece IP'yi içeren temiz sözlük – hosts_manager ve UpdateResult için
            ip_map: dict[str, str | None] = {
                domain: ip for domain, (ip, _) in raw.items()
            }

            resolved = sum(1 for ip in ip_map.values() if ip)
            failed   = len(DOMAINS) - resolved

            for domain, (ip, err) in raw.items():
                if ip:
                    self.log_message.emit(f"  {domain}  →  {ip}", "success")
                else:
                    reason = err.split("—")[-1].strip() if err else "bilinmeyen hata"
                    self.log_message.emit(
                        f"  {domain}  →  hata: {reason}", "warning"
                    )

            if failed:
                self.log_message.emit(
                    f"{failed} domain çözümlenemedi, atlandı.", "warning"
                )

            # 3) Tum Discord domainlerini SNI proxy uzerinden yonlendir.
            # ISP, TLS ClientHello icindeki SNI'yi TCP RST ile kesiyor;
            # proxy bu paketi 2 byte'lik parcalara bolerek gonderir.
            proxy = get_proxy()
            if proxy.is_running():
                bound = proxy.bound_host   # 127.0.0.1 veya 127.0.0.2 vb.
                routed = []
                for domain, ip in list(ip_map.items()):
                    if ip and ip != bound:
                        proxy.update_domain_map({domain: ip})
                        ip_map[domain] = bound
                        routed.append(domain)
                if routed:
                    self.log_message.emit(
                        f"SNI bypass: {len(routed)} domain {bound} uzerinden yonlendirildi.",
                        "success"
                    )

            self.log_message.emit("Hosts dosyası güncelleniyor...", "info")
            written = update_hosts(ip_map)
            self.log_message.emit(
                f"{len(written)} domain hosts dosyasına yazıldı.", "success"
            )

            # 4) DNS cache temizle
            self.log_message.emit("DNS önbelleği temizleniyor...", "info")
            ok = flush_dns_cache()
            if ok:
                self.log_message.emit("DNS önbelleği temizlendi.", "success")
            else:
                self.log_message.emit("DNS önbelleği temizlenemedi.", "warning")

            # 5) Bağlantı testi
            self.log_message.emit("Discord bağlantısı test ediliyor...", "info")
            connected, latency = check_discord_connectivity()

            if connected:
                self.log_message.emit(
                    f"Discord erişilebilir ✓  Ping: {latency} ms", "success"
                )
            else:
                self.log_message.emit(
                    "Discord'a ulaşılamadı. ISP SNI/DPI bloğu olabilir.", "warning"
                )

            result = UpdateResult(
                success=True,
                ip_map=ip_map,
                connected=connected,
                latency=latency,
                message=f"{resolved} domain başarıyla güncellendi.",
            )

            # 6) Otomatik Discord yeniden başlatma (etkinleştirilmişse)
            if self._auto_restart_discord and result.success:
                self.log_message.emit("Discord yeniden başlatılıyor...", "info")
                info = restart_discord(wait_seconds=2.0)
                if info["was_running"]:
                    if info["relaunched"]:
                        self.log_message.emit(
                            "Discord yeniden başlatıldı ✓", "success"
                        )
                    else:
                        self.log_message.emit(
                            "Discord kapatıldı fakat yeniden başlatılamadı.", "warning"
                        )
                else:
                    self.log_message.emit(
                        "Discord zaten kapalıydı, atlandı.", "info"
                    )

        except HostsManagerError as e:
            self.log_message.emit(f"Hosts hatası: {e}", "error")
            result = UpdateResult(
                success=False, ip_map={},
                connected=False, latency=-1.0, message=str(e),
            )
        except Exception as e:
            self.log_message.emit(f"Beklenmeyen hata: {e}", "error")
            result = UpdateResult(
                success=False, ip_map={},
                connected=False, latency=-1.0, message=str(e),
            )

        self.update_finished.emit(result)
