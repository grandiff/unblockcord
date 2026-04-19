"""
UnblockCord — Configuration
Discord domainleri ve uygulama ayarları.
"""

import os
import json
from pathlib import Path

# ---------------------------------------------------------------------------
# Discord domain listesi
# ---------------------------------------------------------------------------
DOMAINS = [
    "discord.com",
    "discordapp.com",
    "gateway.discord.gg",
    "cdn.discordapp.com",
    "media.discordapp.net",
    "dl.discordapp.net",       # Güncelleme dosyası CDN'i
    "updates.discord.com",
    "status.discord.com",
]

# ---------------------------------------------------------------------------
# Hosts dosyası
# ---------------------------------------------------------------------------
HOSTS_FILE = r"C:\Windows\System32\drivers\etc\hosts"
HOSTS_MARKER_START = "# === UnblockCord START ==="
HOSTS_MARKER_END   = "# === UnblockCord END ==="

# ---------------------------------------------------------------------------
# DNS over HTTPS (Cloudflare + Google fallback)
# ---------------------------------------------------------------------------
DOH_PRIMARY  = "https://cloudflare-dns.com/dns-query"
DOH_FALLBACK = "https://dns.google/resolve"
DNS_TIMEOUT  = 8  # saniye

# ---------------------------------------------------------------------------
# Bağlantı testi
# ---------------------------------------------------------------------------
CONNECTIVITY_TEST_DOMAIN = "discord.com"
CONNECTIVITY_TEST_PORT   = 443
CONNECTIVITY_TIMEOUT     = 5  # saniye

# ---------------------------------------------------------------------------
# Güncelleme aralıkları  {görüntü adı: saat}
# ---------------------------------------------------------------------------
INTERVALS: dict[str, int] = {
    "30 Dakika":          0.5,
    "1 Saat":             1,
    "3 Saat":             3,
    "6 Saat (Önerilen)":  6,
    "12 Saat":            12,
    "24 Saat":            24,
}
DEFAULT_INTERVAL = "6 Saat (Önerilen)"

# ---------------------------------------------------------------------------
# Kullanıcı ayarları (AppData\Roaming\UnblockCord)
# ---------------------------------------------------------------------------
SETTINGS_DIR  = Path(os.getenv("APPDATA", "~")) / "UnblockCord"
SETTINGS_FILE = SETTINGS_DIR / "settings.json"


def load_settings() -> dict:
    """Ayarları diskten yükle; yoksa varsayılanları döndür."""
    defaults = {
        "interval":          DEFAULT_INTERVAL,
        "autostart":         False,
        "minimize_to_tray":  True,
        "start_minimized":   False,
    }
    try:
        if SETTINGS_FILE.exists():
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            defaults.update(data)
    except Exception:
        pass
    return defaults


def save_settings(settings: dict) -> None:
    """Ayarları diske kaydet."""
    try:
        SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
    except Exception:
        pass
