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
    Discord'a TCP bağlantısı kurarak erişilebilirliği ölçer.

    Returns:
        (başarılı: bool, gecikme_ms: float)
        Başarısız olursa gecikme -1.0 döner.
    """
    start = time.monotonic()
    try:
        sock = socket.create_connection(
            (CONNECTIVITY_TEST_DOMAIN, CONNECTIVITY_TEST_PORT),
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
