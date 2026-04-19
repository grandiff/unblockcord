"""
UnblockCord — Windows Autostart Manager
Uygulamayi Windows baslangicindan otomatik baslatmak icin
HKEY_CURRENT_USER registry anahtarini yonetir.
"""

import sys
import os
import winreg

_REG_KEY   = r"Software\Microsoft\Windows\CurrentVersion\Run"
_APP_NAME  = "UnblockCord"


def _exe_path() -> str:
    """Calistirilabilir dosyanin tam yolunu dondur."""
    if getattr(sys, "frozen", False):
        # PyInstaller ile derlenmis .exe
        return f'"{sys.executable}"'
    # Gelistirme modunda: python main.py
    main_py = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "main.py",
    )
    return f'"{sys.executable}" "{main_py}"'


def is_autostart_enabled() -> bool:
    """Autostart kayit defterinde kayitli mi?"""
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, _REG_KEY, 0, winreg.KEY_READ
        )
        winreg.QueryValueEx(key, _APP_NAME)
        winreg.CloseKey(key)
        return True
    except FileNotFoundError:
        return False
    except Exception:
        return False


def set_autostart(enabled: bool) -> bool:
    """
    Autostart'i etkinlestir ya da devre disi birak.

    Returns:
        True basarili, False hata.
    """
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, _REG_KEY,
            0, winreg.KEY_SET_VALUE
        )
        if enabled:
            winreg.SetValueEx(key, _APP_NAME, 0, winreg.REG_SZ, _exe_path())
        else:
            try:
                winreg.DeleteValue(key, _APP_NAME)
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
        return True
    except Exception:
        return False
