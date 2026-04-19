<div align="center">

<img src="assets/icon.png" width="96" height="96" alt="UnblockCord Logo"/>

# UnblockCord

**Türkiye'deki Discord ISP engelini aşan, VPN gerektirmeyen masaüstü uygulaması.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.11+](https://img.shields.io/badge/Python-3.11%2B-yellow.svg)](https://python.org)
[![Platform: Windows](https://img.shields.io/badge/Platform-Windows%2010%2F11-informational.svg)]()
[![Release](https://img.shields.io/github/v/release/grandiff/unblockcord?label=Son%20S%C3%BCr%C3%BCm)](../../releases)

[📥 İndir](#-hızlı-başlangıç) · [🛠️ Nasıl Çalışır?](#️-nasıl-çalışır) · [📂 Proje Yapısı](#-proje-yapısı)

</div>

---

## ✨ Özellikler

| Özellik | Açıklama |
|---|---|
| 🔀 **DNS Bypass** | Cloudflare DoH ile gerçek IP'leri çeker, sistem `hosts` dosyasına yazar |
| 🛡️ **SNI / DPI Bypass** | ISP paket incelemesini (RST saldırısı) TLS fragmentasyonuyla aşar |
| 🔄 **Otomatik Güncelleme** | Seçilen aralıkta (30dk – 24s) IP'leri günceller |
| 🌐 **Çoklu ISP Desteği** | Türk Telekom, Turkcell, Vodafone — DPI filtreleri dahil tümü |
| 🖥️ **Modern Arayüz** | Discord temalı koyu GUI, domain tablosu, renkli log paneli |
| 📌 **Sistem Tepsisi** | Arka planda çalışır, anlık durum rengi gösterir |
| 🛡️ **Hosts Yedekleme** | İlk çalıştırmada `hosts` dosyasını otomatik yedekler |
| ↩️ **Tek Tık Geri Alma** | Tüm girişleri temizler, sistemi orijinal haline getirir |
| ⚡ **Sıfır Bağımlılık** | Sadece tek bir `.exe` — Python kurulumu gerekmez |

---

## 🚀 Hızlı Başlangıç

### Yol 1 — Hazır `.exe` (Önerilen)

1. [**Releases**](../../releases) sayfasından `UnblockCord.exe` dosyasını indirin
2. Çalıştırın — **UAC yönetici izni** isteyecektir, "Evet" deyin  
   *(Hosts dosyası ve port 443 için gereklidir)*
3. Uygulama otomatik olarak çalışmaya başlar, Discord'u açın

### Yol 2 — Kaynak koddan çalıştırma

**Gereksinim:** Python 3.11+

```bash
git clone https://github.com/grandiff/unblockcord.git
cd unblockcord

pip install -r requirements.txt

# Yönetici terminaliyle çalıştır
python main.py
```

### Yol 3 — Kendi `.exe`'ni derle

```bash
pip install -r requirements.txt
python build.py
# → dist/UnblockCord.exe
```

---

## 🛠️ Nasıl Çalışır?

Türkiye'deki Discord engeli **iki katmanlıdır:**

```
Katman 1 — DNS Engeli:
  discord.com ──► ISP DNS ──► "Engellendi" ✗

Katman 2 — SNI/DPI Engeli:
  discord.com ──► Cloudflare IP ──► TLS ClientHello ──► ISP RST gönderir ✗
```

UnblockCord her iki katmanı da aşar:

### 1️⃣ DNS Bypass — `hosts` dosyası

- **Cloudflare DoH** (`cloudflare-dns.com/dns-query`) veya **Google DoH** üzerinden gerçek IP'leri çeker
- `C:\Windows\System32\drivers\etc\hosts` dosyasına yazar
- Sistem DNS'i hiç devreye girmez — ISP DNS bloğu tamamen atlanır

### 2️⃣ SNI / DPI Bypass — Lokal TLS Proxy

Bazı ISP'ler (Turkcell, Türk Telekom vb.) **TLS ClientHello** paketindeki SNI alanını okuyarak TCP RST gönderir. Bu durumda hosts düzeltmesi tek başına yetmez.

UnblockCord, `127.0.0.x:443` üzerinde lokal bir **şeffaf TCP proxy** çalıştırır:

```
Discord ──► 127.0.0.1:443 (proxy) ──► TLS ClientHello'yu 2 byte'lık
                                       parçalara böler ──► Cloudflare ✓
                                       ISP parçaları birleştiremez,
                                       SNI'yi göremez ──► bağlantıya izin verir ✓
```

Bu yöntem, GoodbyeDPI'nin kullandığı TCP fragmentation tekniğinin saf Python implementasyonudur — **dış binary indirmez.**

> **Port fallback:** `127.0.0.1:443` başka bir uygulama tarafından kullanılıyorsa, `127.0.0.2` → `127.0.0.3` ... `127.0.0.10` sırayla denenir. Windows'ta tüm `127.x.x.x` bloğu loopback adresidir.

---

## 📂 Proje Yapısı

```
unblockcord/
├── main.py                    # Giriş noktası (UAC + PyQt6 başlatma)
├── build.py                   # PyInstaller build scripti
├── requirements.txt
├── assets/
│   └── icon.png
└── app/
    ├── config.py              # Domain listesi, ayarlar, sabitler
    ├── core/
    │   ├── dns_resolver.py    # Cloudflare DoH + Google DoH + nslookup fallback
    │   ├── hosts_manager.py   # Hosts dosyası okuma/yazma/yedekleme
    │   ├── connectivity.py    # Bağlantı testi + DNS cache temizleme
    │   ├── daemon.py          # Arka plan güncelleme thread'i (PyQt6 QThread)
    │   ├── discord_manager.py # Discord süreç yönetimi (başlatma/kapama)
    │   └── sni_proxy.py       # Lokal TLS fragmentasyon proxy'si
    └── ui/
        ├── main_window.py     # Ana pencere (PyQt6)
        ├── tray_icon.py       # Sistem tepsisi ikonu
        └── styles.py          # QSS koyu tema
```

---

## 🔒 Güvenlik & Gizlilik

- Uygulama **hiçbir veri toplamaz**, telemetri içermez
- İnternet bağlantısı **yalnızca** DoH DNS sorgusu için kullanılır
- Tüm işlemler yerel makinenizde gerçekleşir
- Kaynak kodu tamamen açıktır — satır satır inceleyebilirsiniz

---

## ⚠️ Yasal Uyarı

Bu araç yalnızca **meşru erişim hakları bulunan platformlara** erişim için tasarlanmıştır. Kullanıcı, yerel yasalara uygunluk konusunda tamamen sorumludur.

---

## 📜 Lisans

[MIT License](LICENSE) — dilediğiniz gibi kullanabilir, değiştirebilir ve dağıtabilirsiniz.

---

## 🤝 Katkı

PR ve issue'lar açıktır. Yeni domain eklemek, hata bildirmek veya özellik önermek için bir **Issue** açın.
