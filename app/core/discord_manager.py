"""
UnblockCord — Discord Process Manager
Discord masaustu uygulamasini yeniden baslatir.
"""

import subprocess
import time
import os
import winreg
from pathlib import Path


def find_discord_exe() -> list[str]:
    """
    Discord.exe yollarini bul.
    Birden fazla kurulum (stable, canary, ptb) olabilir.
    """
    candidates: list[str] = []

    # 1) %LOCALAPPDATA%\Discord klasoru
    local_app = os.environ.get("LOCALAPPDATA", "")
    for variant in ["Discord", "DiscordCanary", "DiscordPTB"]:
        base = Path(local_app) / variant
        if base.exists():
            # En yeni Update klasorundeki exe'yi bul
            for update_dir in sorted(base.glob("app-*"), reverse=True):
                exe = update_dir / "Discord.exe"
                if exe.exists():
                    candidates.append(str(exe))
                    break

    # 2) Kayit defterinden bul (fallback)
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Uninstall\Discord",
        )
        path, _ = winreg.QueryValueEx(key, "DisplayIcon")
        winreg.CloseKey(key)
        if path and Path(path).exists():
            candidates.append(path)
    except Exception:
        pass

    return candidates


def kill_discord() -> int:
    """
    Tum Discord.exe sureclerini sonlandir.
    Returns: sonlandirilan surec sayisi
    """
    result = subprocess.run(
        ["taskkill", "/F", "/IM", "Discord.exe"],
        capture_output=True,
        text=True,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    # "1 processe(s) [...] terminated" gibi bir cikti
    count = result.stdout.lower().count("terminated")
    return count


def is_discord_running() -> bool:
    """Discord.exe surecinin calisip calismadigini kontrol et."""
    result = subprocess.run(
        ["tasklist", "/FI", "IMAGENAME eq Discord.exe", "/NH"],
        capture_output=True,
        text=True,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    return "discord.exe" in result.stdout.lower()


def launch_discord() -> bool:
    """
    Discord'u baslatmaya calis.
    Returns: True basarili, False bulunamadi.
    """
    exes = find_discord_exe()
    if not exes:
        return False

    try:
        subprocess.Popen(
            [exes[0]],
            creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
        )
        return True
    except Exception:
        return False


def restart_discord(wait_seconds: float = 1.5) -> dict:
    """
    Discord'u yeniden baslatir: once oldurur, sonra baslatir.

    Returns:
        {
            "was_running": bool,
            "killed": int,       # sonlandirilan surec sayisi
            "relaunched": bool,
        }
    """
    was_running = is_discord_running()
    killed = 0

    if was_running:
        killed = kill_discord()
        time.sleep(wait_seconds)

    relaunched = launch_discord()
    return {
        "was_running": was_running,
        "killed":      killed,
        "relaunched":  relaunched,
    }
