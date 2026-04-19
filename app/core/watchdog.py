"""
UnblockCord — Connection Watchdog
Arkaplanda Discord baglanabilirligini izler.
Baglanti kopunca daemon'a zorla guncelleme tetikler,
UI'ya bildirim sinyali gonderir.
"""

from PyQt6.QtCore import QThread, pyqtSignal

from app.core.connectivity import check_discord_connectivity
from app.core.sni_proxy    import get_proxy


_POLL_INTERVAL_MS  = 60_000   # 60 saniyede bir kontrol
_FAIL_THRESHOLD    = 2        # Art arda kac basarisizlikta alarm


class WatchdogThread(QThread):
    """
    Periyodik olarak Discord'a TCP baglantisi test eder.
    Art arda FAIL_THRESHOLD kadar basarisizlik olursa:
      - connection_lost  sinyali gonderir
      - reconnect_needed sinyali gonderir (daemon guncellemeyi tetikler)
    Baglanti geri gelince connection_restored sinyali gonderir.
    """

    connection_lost     = pyqtSignal()          # baglanti koptu
    connection_restored = pyqtSignal(float)     # baglanti geldi (latency_ms)
    reconnect_needed    = pyqtSignal()          # daemon'a guncelleme tetikle
    status_update       = pyqtSignal(bool, float)  # (connected, latency)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._running     = False
        self._was_ok      = True   # son bilinen durum
        self._fail_count  = 0

    def stop(self) -> None:
        self._running = False
        self.wait(3000)

    def run(self) -> None:
        self._running = True

        while self._running:
            proxy = get_proxy()
            if proxy.is_running():
                ok, lat = check_discord_connectivity()
            else:
                # Proxy calismiyorsa test yapma
                self.msleep(_POLL_INTERVAL_MS)
                continue

            self.status_update.emit(ok, lat)

            if ok:
                self._fail_count = 0
                if not self._was_ok:
                    # Baglanti geri geldi
                    self._was_ok = True
                    self.connection_restored.emit(lat)
            else:
                self._fail_count += 1
                if self._fail_count >= _FAIL_THRESHOLD:
                    if self._was_ok:
                        # Ilk kopma
                        self._was_ok = False
                        self.connection_lost.emit()
                    # Her FAIL_THRESHOLD basarisizliktan sonra guncelleme iste
                    if self._fail_count % _FAIL_THRESHOLD == 0:
                        self.reconnect_needed.emit()

            self.msleep(_POLL_INTERVAL_MS)
