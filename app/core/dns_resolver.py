"""
UnblockCord — DNS Resolver
3 kademeli çözümleme:
  1. Cloudflare DoH (HTTPS)
  2. Google DoH   (HTTPS)
  3. nslookup 1.1.1.1 (subprocess — elevated admin'de de çalışır)
"""

import re
import subprocess
from typing import Optional

import requests

from app.config import DOH_PRIMARY, DOH_FALLBACK, DNS_TIMEOUT


class DNSResolveError(Exception):
    """Tüm yöntemler başarısız olduğunda fırlatılır."""
    pass


# ---------------------------------------------------------------------------
# Yardımcı: nslookup fallback
# ---------------------------------------------------------------------------

def _resolve_via_nslookup(domain: str) -> Optional[str]:
    """
    Subprocess nslookup komutuyla 1.1.1.1 DNS sunucusunu kullanarak çözümle.
    Elevated admin sürecinde HTTPS istek sorununu bypass eder.
    """
    _IPV4 = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")
    try:
        result = subprocess.run(
            ["nslookup", domain, "1.1.1.1"],
            capture_output=True,
            text=True,
            timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        lines = result.stdout.splitlines()

        # "Address:" içeren satırları topla (# işareti olmayan = port yok = saf IP)
        ips: list[str] = []
        for line in lines:
            if "Address:" in line and "#" not in line:
                ip = line.split("Address:")[-1].strip()
                if _IPV4.match(ip):
                    ips.append(ip)

        # İlk kayıt DNS sunucusunun IP'si (1.1.1.1); ikincisi ve sonrası hedef IP
        for ip in ips:
            if ip != "1.1.1.1":
                return ip

    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# Ana çözümleyici
# ---------------------------------------------------------------------------

def resolve_domain(domain: str) -> str:
    """
    Üç kademeli DNS çözümlemesi:
      1. Cloudflare DoH
      2. Google DoH
      3. nslookup 1.1.1.1 (subprocess fallback)

    Args:
        domain: Çözümlenecek domain (örn. "discord.com")

    Returns:
        IPv4 adresi (string).

    Raises:
        DNSResolveError: Tüm yöntemler başarısız olursa.
    """
    last_error = "bilinmeyen hata"

    def _doh_get(url: str, verify: bool) -> list[str]:
        """Tek bir DoH isteği yap; A kayıtlarını döndür."""
        resp = requests.get(
            url,
            params={"name": domain, "type": "A"},
            headers={"Accept": "application/dns-json"},
            timeout=DNS_TIMEOUT,
            verify=verify,
        )
        resp.raise_for_status()
        return [
            a["data"]
            for a in resp.json().get("Answer", [])
            if a.get("type") == 1
        ]

    # ── 1 & 2: DoH denemeleri (önce SSL doğrulamalı, sonra verify=False) ──
    for url in [DOH_PRIMARY, DOH_FALLBACK]:
        for verify in (True, False):          # Kaspersky/antivirus SSL hatası için fallback
            try:
                if not verify:
                    import urllib3
                    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                records = _doh_get(url, verify)
                if records:
                    return records[0]
                last_error = f"DoH yanıtında A kaydı bulunamadı ({url})"
                break                          # Kayıt yok → sonraki URL'yi dene
            except requests.exceptions.SSLError:
                continue                       # SSL hatası → verify=False ile tekrar dene
            except Exception as e:
                last_error = f"{type(e).__name__}: {e}"
                break                          # Başka hata → sonraki URL'yi dene

    # ── 3: nslookup fallback ────────────────────────────────────────────
    ip = _resolve_via_nslookup(domain)
    if ip:
        return ip

    raise DNSResolveError(
        f"{domain} çözümlenemedi — son hata: {last_error}"
    )


def resolve_all(
    domains: list[str],
) -> dict[str, tuple[Optional[str], Optional[str]]]:
    """
    Birden fazla domain'i çözer.

    Args:
        domains: Domain adları listesi.

    Returns:
        {domain: (ip_veya_None, hata_mesajı_veya_None)} sözlüğü.
    """
    results: dict[str, tuple[Optional[str], Optional[str]]] = {}
    for domain in domains:
        try:
            results[domain] = (resolve_domain(domain), None)
        except DNSResolveError as e:
            results[domain] = (None, str(e))
    return results
