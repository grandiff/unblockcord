"""
UnblockCord — Connectivity Checker
Discord'a TCP bağlantısı kurarak erişilebilirliği test eder.
Hosts dosyasını dikkate alır (sistem DNS'i kullanır).
"""

import socket
import subprocess
import time

from app.config import (
    CONNECTIVITY_TEST_DOMAIN,
    CONNECTIVITY_TEST_PORT,
    CONNECTIVITY_TIMEOUT,
)


def check_discord_connectivity() -> tuple[bool, float]:
    """
    Discord'a TCP baglanabilirligini olcer.
    Proxy map'ten gercek Cloudflare IP'sini kullanir
    (hosts dosyasi 127.0.0.1 gosterdigi icin).

    Returns:
        (basarili: bool, gecikme_ms: float)
        Basarisiz olursa gecikme -1.0 doner.
    """
    # Gercek IP'yi proxy map'ten bul
    target = CONNECTIVITY_TEST_DOMAIN
    try:
        from app.core.sni_proxy import get_proxy
        proxy = get_proxy()
        real_ip = proxy._ip_map.get(target)
        if real_ip:
            target = real_ip
    except Exception:
        pass

    start = time.monotonic()
    try:
        sock = socket.create_connection(
            (target, CONNECTIVITY_TEST_PORT),
            timeout=CONNECTIVITY_TIMEOUT,
        )
        sock.close()
        latency_ms = (time.monotonic() - start) * 1000
        return True, round(latency_ms, 1)
    except (socket.timeout, socket.error, OSError):
        return False, -1.0


def flush_dns_cache() -> bool:
    """
    Windows DNS çözümleyici önbelleğini temizler (ipconfig /flushdns).

    Returns:
        True: başarılı, False: başarısız.
    """
    try:
        result = subprocess.run(
            ["ipconfig", "/flushdns"],
            capture_output=True,
            text=True,
            timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        return result.returncode == 0
    except Exception:
        return False
