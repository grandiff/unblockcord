"""
UnblockCord — Local SNI Bypass Proxy
Saf Python ile TLS ClientHello fragmentation.

Nasil calisir:
  1. 127.0.0.1:443 uzerinde TCP sunucu acar (admin gerektiriyor — zaten admin).
  2. Hosts dosyasina 127.0.0.1 → updates.discord.com yazilir.
  3. Discord'un updater'i 127.0.0.1:443'e baglanir (updates.discord.com sanarak).
  4. Biz gercek IP'ye (DoH ile cozulmus Cloudflare IP) baglanir,
     TLS ClientHello'yu 2-byte parcalara bolup gonderiyoruz.
  5. ISP, parcalanmis paketleri birlestiremez -> SNI'yi goemez -> izin verir.
  6. Cloudflare gercek ClientHello'yu alir, TLS kurar, is biter.
"""

import socket
import struct
import threading
from typing import Optional


# ---------------------------------------------------------------------------
# Sabiltler
# ---------------------------------------------------------------------------

PROXY_PORT       = 443
FRAG_SIZE        = 2          # TLS ClientHello kac byte'lik parcalara bolunecek
TIMEOUT_SEC      = 15

# Eger 127.0.0.1:443 mesgulse, sirayla diger loopback IP'leri dene.
# Windows'ta 127.x.x.x blogunun tamami loopback adres olarak calisir.
_PROXY_CANDIDATES = [f"127.0.0.{i}" for i in range(1, 11)]


# ---------------------------------------------------------------------------
# TLS ayrıştırıcı — SNI cıkarma
# ---------------------------------------------------------------------------

def _extract_sni(data: bytes) -> Optional[str]:
    """
    TLS ClientHello baytlarindan SNI hostname'ini cikarir.
    Basarisiz olursa None doner.
    """
    try:
        if len(data) < 5 or data[0] != 0x16:   # TLS Handshake record
            return None

        # TLS record header: 1 tip + 2 surum + 2 uzunluk = 5 byte
        # Handshake header:  1 tip + 3 uzunluk                = 4 byte
        # ProtocolVersion:   2 byte
        # Random:            32 byte
        pos = 5 + 4 + 2 + 32

        if pos >= len(data):
            return None

        session_id_len = data[pos]                      # Session ID
        pos += 1 + session_id_len

        if pos + 2 > len(data):
            return None

        cs_len = struct.unpack_from("!H", data, pos)[0] # Cipher Suites
        pos += 2 + cs_len

        if pos + 1 > len(data):
            return None

        comp_len = data[pos]                            # Compression Methods
        pos += 1 + comp_len

        if pos + 2 > len(data):
            return None

        ext_total = struct.unpack_from("!H", data, pos)[0]
        pos += 2
        ext_end = pos + ext_total

        while pos + 4 <= min(ext_end, len(data)):
            ext_type = struct.unpack_from("!H", data, pos)[0]
            ext_len  = struct.unpack_from("!H", data, pos + 2)[0]
            pos += 4

            if ext_type == 0x0000:  # server_name extension
                # 2 byte list len, 1 byte name type, 2 byte name len, name
                if pos + 5 <= len(data):
                    name_len = struct.unpack_from("!H", data, pos + 3)[0]
                    if pos + 5 + name_len <= len(data):
                        return data[pos + 5 : pos + 5 + name_len].decode(
                            "utf-8", errors="ignore"
                        )
            pos += ext_len

    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# Proxy sunucusu
# ---------------------------------------------------------------------------

class SNIProxy:
    """
    Lokal transparent TLS proxy:
    - TLS ClientHello'yu kucuk parcalara boler -> ISP SNI'yi goremez
    - Gercek IP'ye yonlendirir (hosts dosyasini atlayarak dogrudan IP)
    """

    def __init__(self) -> None:
        self._server:     Optional[socket.socket] = None
        self._running     = False
        self._lock        = threading.Lock()
        self._ip_map:     dict[str, str] = {}   # domain -> gercek IP
        self._bound_host: str = "127.0.0.1"     # basarili bind adresi

    @property
    def bound_host(self) -> str:
        """Proxy'nin dinledigi loopback IP adresi."""
        return self._bound_host

    # ── Public API ──────────────────────────────────────────────────────

    def update_domain_map(self, ip_map: dict[str, str]) -> None:
        """Hangi domainlerin hangi gercek IP'ye yonlendirielcegini guncelle."""
        with self._lock:
            self._ip_map.update(ip_map)

    def start(
        self,
        log_cb=None
    ) -> bool:
        """
        Uygun bir loopback adresinde 443 portunu dinemlemeye basla.
        127.0.0.1 mesgulse 127.0.0.2, 127.0.0.3 ... 127.0.0.10 dener.

        Returns:
            True basarili, False tum adresler mesgul / hata.
        """
        def _log(msg: str, level: str = "info") -> None:
            if log_cb:
                log_cb(msg, level)

        for candidate in _PROXY_CANDIDATES:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock.bind((candidate, PROXY_PORT))
                sock.listen(64)
                self._server      = sock
                self._running     = True
                self._bound_host  = candidate
                _log(
                    f"SNI bypass proxy baslatildi -> {candidate}:{PROXY_PORT}",
                    "success"
                )
                threading.Thread(
                    target=self._accept_loop, daemon=True
                ).start()
                return True
            except OSError:
                # Bu adres mesgul, sonrakini dene
                continue

        _log(
            f"SNI proxy: 127.0.0.1-127.0.0.10 araliginda port {PROXY_PORT} \"acik adres bulunamadi.",
            "error"
        )
        return False

    def stop(self, log_cb=None) -> None:
        """Proxy sunucusunu durdur."""
        self._running = False
        if self._server:
            try:
                self._server.close()
            except Exception:
                pass
            self._server = None
        if log_cb:
            log_cb("SNI bypass proxy durduruldu.", "info")

    def is_running(self) -> bool:
        return self._running and self._server is not None

    # ── Ic implementasyon ────────────────────────────────────────────────

    def _accept_loop(self) -> None:
        while self._running:
            try:
                self._server.settimeout(1.0)
                client, addr = self._server.accept()
                threading.Thread(
                    target=self._handle,
                    args=(client,),
                    daemon=True,
                ).start()
            except socket.timeout:
                continue
            except Exception:
                break

    def _handle(self, client: socket.socket) -> None:
        server: Optional[socket.socket] = None
        try:
            client.settimeout(TIMEOUT_SEC)

            # 1) Discord'dan ilk veriyi al (TLS ClientHello)
            hello = client.recv(16384)
            if not hello:
                return

            # 2) SNI'yi cikar
            sni = _extract_sni(hello) or "updates.discord.com"

            # 3) Gercek IP'yi bul (IP map'ten, hosts dosyasini atla)
            with self._lock:
                real_ip = self._ip_map.get(sni)

            if not real_ip:
                # Fallback: en son bilinen Cloudflare IP (updates.discord.com)
                real_ip = "162.159.137.232"

            # 4) Gercek sunucuya baglan (IP ile, hostname ile degil)
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            server.settimeout(TIMEOUT_SEC)
            server.connect((real_ip, 443))
            server.settimeout(None)

            # 5) TLS ClientHello'yu PARCALAYARAK gonder (ISP SNI tespitini atla)
            self._send_fragmented(server, hello)

            # 6) Kalan veriyi iki yonlu aktar
            client.settimeout(None)
            t1 = threading.Thread(
                target=self._pipe, args=(client, server), daemon=True
            )
            t2 = threading.Thread(
                target=self._pipe, args=(server, client), daemon=True
            )
            t1.start()
            t2.start()
            t1.join()
            t2.join()

        except Exception:
            pass
        finally:
            self._close(client)
            self._close(server)

    @staticmethod
    def _send_fragmented(sock: socket.socket, data: bytes) -> None:
        """
        TLS ClientHello'yu FRAG_SIZE'lik parcalara bolup gonder.
        TCP_NODELAY ile her send() ayri TCP segmenti olusturur.
        ISP'nin DPI sistemi parcalari birlestiremez -> SNI gizlenir.
        """
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        for i in range(0, len(data), FRAG_SIZE):
            sock.sendall(data[i : i + FRAG_SIZE])

    @staticmethod
    def _pipe(src: socket.socket, dst: socket.socket) -> None:
        """Iki socket arasinda veri aktarimi (geri kalan trafik icin)."""
        try:
            while True:
                chunk = src.recv(65536)
                if not chunk:
                    break
                dst.sendall(chunk)
        except Exception:
            pass
        finally:
            SNIProxy._close(src)
            SNIProxy._close(dst)

    @staticmethod
    def _close(sock: Optional[socket.socket]) -> None:
        if sock:
            try:
                sock.close()
            except Exception:
                pass


# ---------------------------------------------------------------------------
# Modul seviyesinde singleton
# ---------------------------------------------------------------------------

_proxy = SNIProxy()


def get_proxy() -> SNIProxy:
    return _proxy
