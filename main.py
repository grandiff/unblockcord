"""
UnblockCord — Giriş Noktası
UAC yönetici yetkisi kontrolü ve PyQt6 uygulamasını başlatır.
"""

import sys
import ctypes
import os


def is_admin() -> bool:
    """Mevcut işlemin yönetici yetkisi var mı?"""
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def run_as_admin() -> None:
    """UAC iletişim kutusu açarak uygulamayı yönetici olarak yeniden başlatır."""
    params = " ".join(f'"{arg}"' for arg in sys.argv)
    ctypes.windll.shell32.ShellExecuteW(
        None,           # hwnd
        "runas",        # işlem
        sys.executable, # program
        params,         # argümanlar
        None,           # çalışma dizini
        1,              # SW_SHOWNORMAL
    )


def main() -> None:
    # Hosts dosyasını yazabilmek için yönetici yetkisi şart
    if not is_admin():
        run_as_admin()
        sys.exit(0)

    # PyQt6 importları yönetici onayından sonra yapılır
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtGui     import QIcon
    from app.ui.main_window import MainWindow

    app = QApplication(sys.argv)
    app.setApplicationName("UnblockCord")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("UnblockCord")
    app.setQuitOnLastWindowClosed(False)  # Tepside çalışmaya devam et

    icon_path = os.path.join(os.path.dirname(__file__), "assets", "icon.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
