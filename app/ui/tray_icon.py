"""
UnblockCord — System Tray Icon
Renkli durum göstergesi ve sağ-tık menüsü.
"""

import os

from PyQt6.QtWidgets import QSystemTrayIcon, QMenu
from PyQt6.QtGui    import QIcon, QPixmap, QColor, QPainter, QBrush
from PyQt6.QtCore   import pyqtSignal


class TrayIcon(QSystemTrayIcon):
    """Sistem tepsisi ikonu — durum rengi + context menü."""

    show_window    = pyqtSignal()
    trigger_update = pyqtSignal()
    quit_app       = pyqtSignal()

    _STATUS_COLORS = {
        "connected":    "#57F287",
        "disconnected": "#ED4245",
        "checking":     "#FEE75C",
    }
    _STATUS_TIPS = {
        "connected":    "UnblockCord  —  Discord Erişilebilir ✓",
        "disconnected": "UnblockCord  —  Discord Erişilemiyor ✗",
        "checking":     "UnblockCord  —  Kontrol ediliyor…",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._icon_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "assets", "icon.png",
        )
        self._setup_menu()
        self.set_status("checking")
        self.activated.connect(self._on_activated)

    # ------------------------------------------------------------------

    def _setup_menu(self):
        menu = QMenu()

        title = menu.addAction("🔓  UnblockCord")
        title.setEnabled(False)
        menu.addSeparator()

        open_action   = menu.addAction("📊  Pencereyi Aç")
        update_action = menu.addAction("▶   Şimdi Güncelle")
        menu.addSeparator()
        quit_action   = menu.addAction("✕   Kapat")

        open_action.triggered.connect(self.show_window)
        update_action.triggered.connect(self.trigger_update)
        quit_action.triggered.connect(self.quit_app)

        self.setContextMenu(menu)

    # ------------------------------------------------------------------

    def _make_dot_icon(self, hex_color: str) -> QIcon:
        """Renkli daire ikonu üret (dosya yoksa fallback)."""
        px = QPixmap(32, 32)
        px.fill(QColor(0, 0, 0, 0))
        p = QPainter(px)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setBrush(QBrush(QColor(hex_color)))
        p.setPen(QColor(hex_color))
        p.drawEllipse(4, 4, 24, 24)
        p.end()
        return QIcon(px)

    def set_status(self, status: str) -> None:
        """İkon ve tooltip'i bağlantı durumuna göre güncelle."""
        color = self._STATUS_COLORS.get(status, self._STATUS_COLORS["checking"])

        if os.path.exists(self._icon_path):
            self.setIcon(QIcon(self._icon_path))
        else:
            self.setIcon(self._make_dot_icon(color))

        self.setToolTip(self._STATUS_TIPS.get(status, "UnblockCord"))

    def show_message(self, title: str, body: str) -> None:
        self.showMessage(title, body, QSystemTrayIcon.MessageIcon.Information, 3000)

    # ------------------------------------------------------------------

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_window.emit()
