"""
UnblockCord — Main Window
PyQt6 ana uygulama penceresi.
"""

import os
import threading
from datetime import datetime
from typing import Optional

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QTextEdit, QComboBox, QFrame,
    QHeaderView, QApplication, QCheckBox,
)
from PyQt6.QtCore import Qt, pyqtSlot, QSize
from PyQt6.QtGui  import QIcon, QFont, QColor, QPixmap

from app.config               import DOMAINS, INTERVALS, load_settings, save_settings
from app.core.daemon          import DaemonThread, UpdateResult
from app.core.hosts_manager   import restore_hosts
from app.core.discord_manager import restart_discord
from app.core.sni_proxy       import get_proxy
from app.core.autostart       import is_autostart_enabled, set_autostart
from app.core.watchdog        import WatchdogThread
from app.ui.styles            import MAIN_STYLESHEET, COLORS
from app.ui.tray_icon         import TrayIcon


# ═══════════════════════════════════════════════════════════════════════════
# Yardımcı bileşenler
# ═══════════════════════════════════════════════════════════════════════════

class StatusDot(QLabel):
    _STYLES = {
        "connected":    "color: #57F287; font-size: 16px;",
        "disconnected": "color: #ED4245; font-size: 16px;",
        "checking":     "color: #FEE75C; font-size: 16px;",
    }

    def __init__(self, parent=None):
        super().__init__("●", parent)
        self.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self.set("checking")

    def set(self, status: str):
        self.setStyleSheet(self._STYLES.get(status, self._STYLES["checking"]))


class SectionLabel(QLabel):
    def __init__(self, text: str, parent=None):
        super().__init__(text.upper(), parent)
        self.setStyleSheet(
            f"color: {COLORS['text_secondary']}; "
            f"font-size: 11px; font-weight: 700; letter-spacing: 1px;"
        )


class Divider(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.HLine)
        self.setFixedHeight(1)
        self.setStyleSheet(f"background-color: {COLORS['border']};")


class LogPanel(QTextEdit):
    _COLORS = {
        "info":    COLORS["text_secondary"],
        "success": COLORS["green"],
        "warning": COLORS["yellow"],
        "error":   COLORS["red"],
    }
    _ICONS = {
        "info":    "→",
        "success": "✓",
        "warning": "⚠",
        "error":   "✗",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setMinimumHeight(150)
        self.setMaximumHeight(200)

    def append_log(self, message: str, level: str = "info") -> None:
        ts    = datetime.now().strftime("%H:%M:%S")
        color = self._COLORS.get(level, self._COLORS["info"])
        icon  = self._ICONS.get(level, "→")
        html  = (
            f'<span style="color:{COLORS["text_muted"]};">[{ts}]</span>&nbsp;'
            f'<span style="color:{color}; font-weight:600;">{icon}</span>&nbsp;'
            f'<span style="color:{color};">{message}</span>'
        )
        self.append(html)
        self.ensureCursorVisible()


# ═══════════════════════════════════════════════════════════════════════════
# Ana pencere
# ═══════════════════════════════════════════════════════════════════════════

class MainWindow(QMainWindow):
    """UnblockCord ana uygulama penceresi."""

    APP_VERSION = "1.1.0"

    def __init__(self):
        super().__init__()
        self.settings: dict = load_settings()
        self._last_result: Optional[UpdateResult] = None

        self._init_window()
        self._init_daemon()
        self._init_watchdog()
        self._build_ui()
        self._init_tray()
        self._apply_initial_settings()

    # ─── Başlatma ────────────────────────────────────────────────────────

    def _init_window(self):
        self.setWindowTitle(f"UnblockCord  v{self.APP_VERSION}")
        self.setMinimumSize(800, 660)
        self.resize(840, 700)
        self.setStyleSheet(MAIN_STYLESHEET)

        icon_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "assets", "icon.png",
        )
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        screen = QApplication.primaryScreen()
        if screen:
            sg = screen.availableGeometry()
            self.move((sg.width() - 840) // 2, (sg.height() - 700) // 2)

    def _init_daemon(self):
        self.daemon = DaemonThread(self)
        self.daemon.update_started.connect(self._on_update_started)
        self.daemon.update_finished.connect(self._on_update_finished)
        self.daemon.log_message.connect(self._on_log_message)
        self.daemon.countdown_tick.connect(self._on_countdown_tick)
        self.daemon.set_interval(self.settings.get("interval", "6 Saat (Önerilen)"))
        self.daemon.start()

    def _init_watchdog(self):
        self.watchdog = WatchdogThread(self)
        self.watchdog.connection_lost.connect(self._on_connection_lost)
        self.watchdog.connection_restored.connect(self._on_connection_restored)
        self.watchdog.reconnect_needed.connect(self.daemon.trigger_update)
        self.watchdog.start()

    def _init_tray(self):
        self.tray = TrayIcon(self)
        self.tray.show_window.connect(self._show_and_raise)
        self.tray.trigger_update.connect(self._on_manual_update)
        self.tray.quit_app.connect(self._on_quit)
        self.tray.show()

    def _apply_initial_settings(self):
        interval = self.settings.get("interval", "6 Saat (Önerilen)")
        idx = self.interval_combo.findText(interval)
        if idx >= 0:
            self.interval_combo.setCurrentIndex(idx)

        auto_restart = self.settings.get("auto_restart_discord", False)
        self.auto_restart_chk.setChecked(auto_restart)
        self.daemon.set_auto_restart_discord(auto_restart)

        autostart = is_autostart_enabled()
        self.autostart_chk.setChecked(autostart)

    # ─── UI inşası ───────────────────────────────────────────────────────

    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        layout.addWidget(self._build_header())
        layout.addWidget(self._build_status_card())
        layout.addWidget(SectionLabel("Domain Durumu"))
        layout.addWidget(self._build_domain_table())
        layout.addWidget(SectionLabel("İşlem Günlüğü"))
        layout.addWidget(self._build_log_panel())
        layout.addWidget(Divider())
        layout.addWidget(self._build_controls())

    # ── Header ──────────────────────────────────────────────────────────

    def _build_header(self) -> QWidget:
        w = QWidget()
        row = QHBoxLayout(w)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(12)

        icon_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "assets", "icon.png",
        )
        icon_lbl = QLabel()
        if os.path.exists(icon_path):
            px = QPixmap(icon_path).scaled(
                44, 44,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            icon_lbl.setPixmap(px)
        else:
            icon_lbl.setText("🔓")
            icon_lbl.setStyleSheet("font-size: 32px;")
        row.addWidget(icon_lbl)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        title = QLabel("UnblockCord")
        title.setStyleSheet(
            f"font-size: 22px; font-weight: 800; color: {COLORS['text_primary']};"
        )
        subtitle = QLabel("Discord Erişim Yöneticisi  ·  Türkiye")
        subtitle.setStyleSheet(f"font-size: 12px; color: {COLORS['text_secondary']};")
        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        row.addLayout(title_col)
        row.addStretch()

        # SNI proxy durum rozeti
        self.proxy_badge = QLabel("● SNI Bypass Aktif")
        self.proxy_badge.setStyleSheet(
            f"background:{COLORS['bg_tertiary']}; color:{COLORS['green']}; "
            f"padding: 4px 12px; border-radius: 10px; font-size: 11px; font-weight:600; "
            f"border: 1px solid {COLORS['green']}33;"
        )
        row.addWidget(self.proxy_badge)

        ver = QLabel(f"v{self.APP_VERSION}")
        ver.setStyleSheet(
            f"background:{COLORS['bg_tertiary']}; color:{COLORS['text_secondary']}; "
            f"padding: 4px 12px; border-radius: 10px; font-size: 11px; "
            f"border: 1px solid {COLORS['border']};"
        )
        row.addWidget(ver)

        return w

    # ── Durum kartı ─────────────────────────────────────────────────────

    def _build_status_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        card.setStyleSheet(
            "QFrame#card {"
            f"  background: qlineargradient("
            f"    x1:0,y1:0,x2:1,y2:0,"
            f"    stop:0 {COLORS['bg_secondary']},"
            f"    stop:1 {COLORS['bg_card']}"
            f"  );"
            f"  border: 1px solid {COLORS['border']};"
            "  border-radius: 14px;"
            "}"
        )

        row = QHBoxLayout(card)
        row.setContentsMargins(22, 18, 22, 18)
        row.setSpacing(14)

        left = QVBoxLayout()
        left.setSpacing(5)

        status_row = QHBoxLayout()
        status_row.setSpacing(8)
        self.status_dot   = StatusDot()
        self.status_label = QLabel("Başlatılıyor…")
        self.status_label.setStyleSheet(
            f"font-size: 17px; font-weight: 700; color:{COLORS['text_primary']};"
        )
        status_row.addWidget(self.status_dot)
        status_row.addWidget(self.status_label)
        status_row.addStretch()

        self.last_update_label = QLabel("Son güncelleme: —")
        self.last_update_label.setStyleSheet(
            f"color:{COLORS['text_secondary']}; font-size: 12px;"
        )

        left.addLayout(status_row)
        left.addWidget(self.last_update_label)
        row.addLayout(left)
        row.addStretch()

        right = QVBoxLayout()
        right.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        right.setSpacing(4)

        self.countdown_label = QLabel("İlk güncelleme bekleniyor…")
        self.countdown_label.setStyleSheet(
            f"color:{COLORS['accent']}; font-size: 12px; font-weight:600;"
        )
        self.countdown_label.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.latency_label = QLabel("Ping: —")
        self.latency_label.setStyleSheet(
            f"color:{COLORS['text_secondary']}; font-size: 12px;"
        )
        self.latency_label.setAlignment(Qt.AlignmentFlag.AlignRight)

        right.addWidget(self.countdown_label)
        right.addWidget(self.latency_label)
        row.addLayout(right)

        return card

    # ── Domain tablosu ──────────────────────────────────────────────────

    def _build_domain_table(self) -> QTableWidget:
        self.table = QTableWidget(len(DOMAINS), 3)
        self.table.setHorizontalHeaderLabels(["Domain", "IP Adresi", "Durum"])

        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        hh.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(1, 165)
        self.table.setColumnWidth(2, 100)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.table.setShowGrid(False)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.table.setAlternatingRowColors(True)
        self.table.setMaximumHeight(230)

        for i, domain in enumerate(DOMAINS):
            d_item = QTableWidgetItem(domain)
            d_item.setForeground(QColor(COLORS["text_primary"]))

            ip_item = QTableWidgetItem("—")
            ip_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            ip_item.setForeground(QColor(COLORS["text_secondary"]))
            ip_item.setFont(QFont("Consolas", 11))

            st_item = QTableWidgetItem("⏳ Bekliyor")
            st_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            st_item.setForeground(QColor(COLORS["yellow"]))

            self.table.setItem(i, 0, d_item)
            self.table.setItem(i, 1, ip_item)
            self.table.setItem(i, 2, st_item)

        return self.table

    # ── Log paneli ───────────────────────────────────────────────────────

    def _build_log_panel(self) -> QWidget:
        w = QWidget()
        col = QVBoxLayout(w)
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(6)

        row = QHBoxLayout()
        row.addStretch()
        clear_btn = QPushButton("Temizle")
        clear_btn.setFixedSize(76, 26)
        clear_btn.setStyleSheet(
            f"QPushButton {{ background:transparent; color:{COLORS['text_secondary']}; "
            f"border:1px solid {COLORS['border']}; border-radius:6px; font-size:11px; }}"
            f"QPushButton:hover {{ color:{COLORS['text_primary']}; }}"
        )
        clear_btn.clicked.connect(lambda: self.log_panel.clear())
        row.addWidget(clear_btn)
        col.addLayout(row)

        self.log_panel = LogPanel()
        col.addWidget(self.log_panel)
        return w

    # ── Kontrol çubuğu ───────────────────────────────────────────────────

    def _build_controls(self) -> QWidget:
        w = QWidget()
        row = QHBoxLayout(w)
        row.setContentsMargins(0, 4, 0, 0)
        row.setSpacing(10)

        # Güncelle
        self.update_btn = QPushButton("▶  Şimdi Güncelle")
        self.update_btn.setFixedHeight(42)
        self.update_btn.clicked.connect(self._on_manual_update)
        row.addWidget(self.update_btn)

        # Discord yeniden başlat
        restart_btn = QPushButton("↺  Discord Yeniden Başlat")
        restart_btn.setObjectName("btn_secondary")
        restart_btn.setFixedHeight(42)
        restart_btn.setToolTip("Discord uygulamasını kapatıp yeniden başlatır")
        restart_btn.clicked.connect(self._on_restart_discord)
        row.addWidget(restart_btn)

        # Geri al
        restore_btn = QPushButton("↩  Geri Al")
        restore_btn.setObjectName("btn_danger")
        restore_btn.setFixedSize(110, 42)
        restore_btn.setToolTip("UnblockCord girişlerini hosts dosyasından kaldır")
        restore_btn.clicked.connect(self._on_restore)
        row.addWidget(restore_btn)

        row.addStretch()

        # Otomatik restart toggle
        self.auto_restart_chk = QCheckBox("Discord'u yeniden başlat")
        self.auto_restart_chk.setStyleSheet(
            f"color:{COLORS['text_secondary']}; font-size:12px;"
        )
        self.auto_restart_chk.setToolTip("Güncelleme sonrası Discord'u otomatik yeniden başlat")
        self.auto_restart_chk.toggled.connect(self._on_auto_restart_toggled)
        row.addWidget(self.auto_restart_chk)

        row.addSpacing(6)

        # Windows ile başlat toggle
        self.autostart_chk = QCheckBox("Windows ile başlat")
        self.autostart_chk.setStyleSheet(
            f"color:{COLORS['text_secondary']}; font-size:12px;"
        )
        self.autostart_chk.setToolTip("Bilgisayar açılınca UnblockCord otomatik başlasın")
        self.autostart_chk.toggled.connect(self._on_autostart_toggled)
        row.addWidget(self.autostart_chk)

        row.addSpacing(10)

        # Güncelleme aralığı
        interval_lbl = QLabel("Aralık:")
        interval_lbl.setStyleSheet(f"color:{COLORS['text_secondary']}; font-size:12px;")
        row.addWidget(interval_lbl)

        self.interval_combo = QComboBox()
        for name in INTERVALS:
            self.interval_combo.addItem(name)
        self.interval_combo.currentTextChanged.connect(self._on_interval_changed)
        row.addWidget(self.interval_combo)

        # Sistem tepsisine küçült
        hide_btn = QPushButton("—")
        hide_btn.setObjectName("btn_secondary")
        hide_btn.setFixedSize(42, 42)
        hide_btn.setToolTip("Sistem tepsisine küçült")
        hide_btn.clicked.connect(self.hide)
        row.addWidget(hide_btn)

        return w

    # ═══════════════════════════════════════════════════════════════════
    # Sinyal slotları
    # ═══════════════════════════════════════════════════════════════════

    @pyqtSlot()
    def _on_update_started(self):
        self.update_btn.setEnabled(False)
        self.update_btn.setText("⏳  Güncelleniyor…")
        self.status_dot.set("checking")
        self.status_label.setText("Güncelleniyor…")
        self.tray.set_status("checking")

        # Proxy durumunu güncelle
        proxy = get_proxy()
        if proxy.is_running():
            self.proxy_badge.setText("● SNI Bypass Aktif")
            self.proxy_badge.setStyleSheet(
                f"background:{COLORS['bg_tertiary']}; color:{COLORS['green']}; "
                f"padding: 4px 12px; border-radius: 10px; font-size: 11px; font-weight:600; "
                f"border: 1px solid {COLORS['green']}33;"
            )
        else:
            self.proxy_badge.setText("○ SNI Bypass Kapalı")
            self.proxy_badge.setStyleSheet(
                f"background:{COLORS['bg_tertiary']}; color:{COLORS['red']}; "
                f"padding: 4px 12px; border-radius: 10px; font-size: 11px; font-weight:600; "
                f"border: 1px solid {COLORS['red']}33;"
            )

    @pyqtSlot(object)
    def _on_update_finished(self, result: UpdateResult):
        self._last_result = result
        self.update_btn.setEnabled(True)
        self.update_btn.setText("▶  Şimdi Güncelle")

        ts = result.timestamp.strftime("%d.%m.%Y  %H:%M:%S")
        self.last_update_label.setText(f"Son güncelleme: {ts}")

        if result.connected:
            self.status_dot.set("connected")
            self.status_label.setText("Discord Erişilebilir  ✓")
            self.tray.set_status("connected")
        else:
            self.status_dot.set("disconnected")
            self.status_label.setText("Discord Erişilemiyor  ✗")
            self.tray.set_status("disconnected")

        if result.latency > 0:
            self.latency_label.setText(f"Ping: {result.latency} ms")
        else:
            self.latency_label.setText("Ping: —")

        proxy = get_proxy()
        bound = proxy.bound_host if proxy.is_running() else "127.0.0.1"

        for i, domain in enumerate(DOMAINS):
            ip = result.ip_map.get(domain)
            if ip:
                display_ip = f"{ip} (proxy)" if ip == bound else ip
                self.table.item(i, 1).setText(display_ip)
                self.table.item(i, 1).setForeground(QColor(COLORS["text_primary"]))
                self.table.item(i, 2).setText("✓  Aktif")
                self.table.item(i, 2).setForeground(QColor(COLORS["green"]))
            else:
                self.table.item(i, 1).setText("—")
                self.table.item(i, 1).setForeground(QColor(COLORS["text_secondary"]))
                self.table.item(i, 2).setText("✗  Hata")
                self.table.item(i, 2).setForeground(QColor(COLORS["red"]))

    @pyqtSlot(str, str)
    def _on_log_message(self, message: str, level: str):
        self.log_panel.append_log(message, level)

    @pyqtSlot(int)
    def _on_countdown_tick(self, seconds: int):
        if seconds <= 0:
            self.countdown_label.setText("Güncelleniyor…")
            return
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        if h > 0:
            txt = f"Sonraki güncelleme: {h}s {m:02d}d {s:02d}s"
        elif m > 0:
            txt = f"Sonraki güncelleme: {m}d {s:02d}s"
        else:
            txt = f"Sonraki güncelleme: {s}s"
        self.countdown_label.setText(txt)

    @pyqtSlot()
    def _on_manual_update(self):
        self.daemon.trigger_update()

    @pyqtSlot()
    def _on_restore(self):
        try:
            restore_hosts()
            self.log_panel.append_log(
                "UnblockCord girişleri hosts dosyasından kaldırıldı.", "warning"
            )
            self.status_dot.set("disconnected")
            self.status_label.setText("Geri Alındı")
            self.tray.set_status("disconnected")
            for i in range(len(DOMAINS)):
                self.table.item(i, 1).setText("—")
                self.table.item(i, 1).setForeground(QColor(COLORS["text_secondary"]))
                self.table.item(i, 2).setText("✗  Kapalı")
                self.table.item(i, 2).setForeground(QColor(COLORS["red"]))
        except Exception as e:
            self.log_panel.append_log(f"Geri alma başarısız: {e}", "error")

    @pyqtSlot()
    def _on_restart_discord(self):
        """Discord uygulamasını manuel olarak yeniden başlat."""
        self.log_panel.append_log("Discord yeniden başlatılıyor...", "info")

        def _do():
            info = restart_discord(wait_seconds=2.0)
            if info["was_running"]:
                if info["relaunched"]:
                    self.log_panel.append_log("Discord yeniden başlatıldı ✓", "success")
                else:
                    self.log_panel.append_log(
                        "Discord kapatıldı ancak başlatılamadı. Manuel başlatın.", "warning"
                    )
            else:
                self.log_panel.append_log(
                    "Discord zaten kapalıydı, başlatılıyor...", "info"
                )
                restart_discord(wait_seconds=0)

        threading.Thread(target=_do, daemon=True).start()

    @pyqtSlot(str)
    def _on_interval_changed(self, name: str):
        self.daemon.set_interval(name)
        self.settings["interval"] = name
        save_settings(self.settings)
        self.log_panel.append_log(f"Güncelleme aralığı: {name}", "info")

    @pyqtSlot(bool)
    def _on_auto_restart_toggled(self, checked: bool):
        self.daemon.set_auto_restart_discord(checked)
        self.settings["auto_restart_discord"] = checked
        save_settings(self.settings)
        state = "etkinleştirildi" if checked else "devre dışı bırakıldı"
        self.log_panel.append_log(
            f"Otomatik Discord yeniden başlatma {state}.", "info"
        )

    @pyqtSlot()
    def _show_and_raise(self):
        self.show()
        self.raise_()
        self.activateWindow()

    @pyqtSlot()
    def _on_quit(self):
        self.watchdog.stop()
        self.daemon.stop()
        QApplication.quit()

    @pyqtSlot(bool)
    def _on_autostart_toggled(self, checked: bool):
        ok = set_autostart(checked)
        state = "etkinleştirildi" if checked else "devre dışı bırakıldı"
        level = "success" if ok else "warning"
        msg   = f"Windows başlangıcı {state}." if ok else "Autostart ayarlanamadı."
        self.log_panel.append_log(msg, level)

    @pyqtSlot()
    def _on_connection_lost(self):
        self.status_dot.set("disconnected")
        self.status_label.setText("Bağlantı Kesildi  ✗")
        self.tray.set_status("disconnected")
        self.tray.show_message(
            "UnblockCord — Bağlantı Kesildi",
            "Discord'a ulaşılamıyor. Otomatik onarılıyor...",
        )
        self.log_panel.append_log(
            "Bağlantı kesildi, otomatik yeniden bağlanılıyor...", "warning"
        )

    @pyqtSlot(float)
    def _on_connection_restored(self, latency: float):
        self.status_dot.set("connected")
        self.status_label.setText("Discord Erişilebilir  ✓")
        self.tray.set_status("connected")
        self.tray.show_message(
            "UnblockCord — Bağlantı Yenilendi",
            f"Discord'a bağlantı yeniden kuruldu. Ping: {latency} ms",
        )
        self.log_panel.append_log(
            f"Bağlantı geri geldi. Ping: {latency} ms", "success"
        )

    # ═══════════════════════════════════════════════════════════════════
    # Pencere olayları
    # ═══════════════════════════════════════════════════════════════════

    def closeEvent(self, event):
        """X tuşu → her zaman tepsiye küçült. Kapamak için tepsi → Kapat."""
        event.ignore()
        self.hide()
        self.tray.show_message(
            "UnblockCord — Arka planda çalışıyor",
            "Discord bypass aktif. Kapatmak için tepsi ikonu → sağ tık → Kapat.",
        )
