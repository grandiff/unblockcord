"""
UnblockCord — Hosts File Manager
Windows hosts dosyasını okur, yazar, yedekler ve geri alır.
"""

import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from app.config import (
    HOSTS_FILE,
    HOSTS_MARKER_START,
    HOSTS_MARKER_END,
    SETTINGS_DIR,
)


class HostsManagerError(Exception):
    """Hosts dosyası işlemleri başarısız olduğunda fırlatılır."""
    pass


# ---------------------------------------------------------------------------
# İç yardımcılar
# ---------------------------------------------------------------------------

def _read_hosts() -> str:
    try:
        with open(HOSTS_FILE, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except PermissionError:
        raise HostsManagerError(
            "Hosts dosyasına erişim reddedildi. Yönetici yetkisi gerekli."
        )
    except FileNotFoundError:
        raise HostsManagerError(f"Hosts dosyası bulunamadı: {HOSTS_FILE}")


def _write_hosts(content: str) -> None:
    try:
        with open(HOSTS_FILE, "w", encoding="utf-8") as f:
            f.write(content)
    except PermissionError:
        raise HostsManagerError(
            "Hosts dosyasına yazma yetkisi yok. Yönetici olarak çalıştırın."
        )


def _strip_unblock_entries(content: str) -> str:
    """Mevcut UnblockCord bloğunu içerikten siler."""
    lines = content.splitlines(keepends=True)
    result: list[str] = []
    inside = False
    for line in lines:
        stripped = line.strip()
        if stripped == HOSTS_MARKER_START:
            inside = True
            continue
        if stripped == HOSTS_MARKER_END:
            inside = False
            continue
        if not inside:
            result.append(line)
    return "".join(result)


# ---------------------------------------------------------------------------
# Genel API
# ---------------------------------------------------------------------------

def backup_hosts() -> Path:
    """
    Mevcut hosts dosyasını yedekler.

    Returns:
        Yedek dosyasının Path'i.
    """
    try:
        SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = SETTINGS_DIR / f"hosts_backup_{ts}.txt"
        shutil.copy2(HOSTS_FILE, backup_path)
        return backup_path
    except Exception as e:
        raise HostsManagerError(f"Yedekleme başarısız: {e}")


def has_existing_backup() -> bool:
    """Daha önce yedek alınmış mı?"""
    if not SETTINGS_DIR.exists():
        return False
    return any(SETTINGS_DIR.glob("hosts_backup_*.txt"))


def update_hosts(ip_map: Dict[str, Optional[str]]) -> List[str]:
    """
    Hosts dosyasını yeni IP adresleriyle günceller.
    Eski UnblockCord girişlerini temizleyip yenilerini yazar.

    Args:
        ip_map: {domain: ip} sözlüğü. None değerli domainler atlanır.

    Returns:
        Başarıyla yazılan domain listesi.
    """
    current  = _read_hosts()
    cleaned  = _strip_unblock_entries(current)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entries: list[str] = []
    written:  list[str] = []

    for domain, ip in ip_map.items():
        if ip:
            entries.append(f"{ip:<20} {domain}")
            written.append(domain)

    if entries:
        block = (
            f"\n{HOSTS_MARKER_START}\n"
            f"# Guncelleme: {timestamp}\n"
            + "\n".join(entries)
            + f"\n{HOSTS_MARKER_END}\n"
        )
        new_content = cleaned.rstrip() + block
    else:
        new_content = cleaned

    _write_hosts(new_content)
    return written


def restore_hosts() -> None:
    """Tüm UnblockCord girişlerini hosts dosyasından kaldırır."""
    current = _read_hosts()
    cleaned = _strip_unblock_entries(current)
    _write_hosts(cleaned.rstrip() + "\n")


def get_current_entries() -> Dict[str, str]:
    """
    Şu an hosts dosyasındaki UnblockCord girişlerini döndürür.

    Returns:
        {domain: ip} sözlüğü.
    """
    try:
        content = _read_hosts()
    except HostsManagerError:
        return {}

    entries: dict[str, str] = {}
    inside = False
    for line in content.splitlines():
        s = line.strip()
        if s == HOSTS_MARKER_START:
            inside = True
            continue
        if s == HOSTS_MARKER_END:
            inside = False
            continue
        if inside and s and not s.startswith("#"):
            parts = s.split()
            if len(parts) >= 2:
                entries[parts[1]] = parts[0]
    return entries
