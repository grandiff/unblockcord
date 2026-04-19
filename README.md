# 🔓 UnblockCord

**Discord'u Türkiye'den VPN veya ek yazılım olmadan, doğrudan hosts dosyası üzerinden erişilebilir kılan otomatik yönetim aracı.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.11+](https://img.shields.io/badge/Python-3.11%2B-yellow.svg)](https://python.org)
[![Platform: Windows](https://img.shields.io/badge/Platform-Windows-informational.svg)]()

---

## ✨ Özellikler

| Özellik | Açıklama |
|---|---|
| 🔄 Otomatik güncelleme | Seçtiğiniz aralıkta (30dk – 24s) Cloudflare DoH'dan güncel IP'leri çeker |
| 🖥️ Modern GUI | Discord temalı koyu arayüz, domain durumu tablosu ve renkli log paneli |
| 📌 Sistem tepsisi | Arka planda çalışır, durum rengiyle anlık bilgi verir |
| 🛡️ İlk kullanımda yedek | `hosts` dosyasını otomatik olarak yedekler |
| ↩️ Geri alma | Tüm girişleri tek tıkla kaldırır |
| ⚡ Sıfır bağımlılık | Kullanıcı tarafında sadece `.exe` dosyası yeterli |

---

## 🚀 Hızlı Başlangıç

### Yol 1 — Hazır `.exe` (Önerilen)

1. [Releases](../../releases) sayfasından `UnblockCord_vX.X.X.exe` dosyasını indirin
2. Çalıştırın — UAC yönetici izni isteyecektir, **Evet** deyin
3. Uygulama hosts dosyasını otomatik güncelleyecek ve sistem tepsisinde çalışmaya başlayacaktır

### Yol 2 — Kaynak koddan çalıştırma

**Gereksinimler:** Python 3.11+

```bash
# Depoyu klonla
git clone https://github.com/KULLANICI_ADI/UnblockCord.git
cd UnblockCord

# Bağımlılıkları yükle
pip install -r requirements.txt

# Yönetici terminali ile çalıştır
python main.py
```

> **Not:** `main.py` otomatik olarak UAC yükseltme ister. Ancak terminali kendiniz yönetici olarak açarsanız UAC penceresi çıkmaz.

### Yol 3 — Kendi `.exe`'ni derle

```bash
pip install -r requirements.txt
python build.py
# dist/UnblockCord.exe oluşur
```

---

## 🛠️ Nasıl Çalışır?

```
Türkiye'de normal kullanıcı:
  discord.com ──► ISP DNS ──► "Engellendi" ✗

UnblockCord kullanıcısı:
  discord.com ──► hosts dosyası ──► 162.159.x.x (Cloudflare) ✓
                   (DNS'e hiç sorulmaz!)
```

1. **Cloudflare DNS over HTTPS** API'sinden Discord'un güncel IP adreslerini çeker (`cloudflare-dns.com/dns-query`)
2. Windows `hosts` dosyasına (`C:\Windows\System32\drivers\etc\hosts`) bu IP'leri yazar
3. `ipconfig /flushdns` ile DNS önbelleğini temizler
4. Discord'a TCP bağlantı testi yaparak erişimi doğrular

BTK'nın bloğu **DNS tabanlıdır.** `hosts` dosyası, OS seviyesinde DNS'den önce okunduğu için blok tamamen bypass edilir.

> ⚠️ **İstisna:** Bazı ISP'ler (örn. Turkcell) ek olarak SNI/DPI uygulayabilir. Bu durumda hosts yöntemi tek başına yeterli olmayabilir.

---

## 📂 Proje Yapısı

```
UnblockCord/
├── main.py                   # Giriş noktası (UAC + PyQt6 başlatma)
├── build.py                  # PyInstaller build scripti
├── requirements.txt
├── assets/
│   └── icon.png
└── app/
    ├── config.py             # Domain listesi, ayarlar
    ├── core/
    │   ├── dns_resolver.py   # Cloudflare DoH API
    │   ├── hosts_manager.py  # Hosts dosyası R/W/yedek
    │   ├── connectivity.py   # Bağlantı testi + DNS flush
    │   └── daemon.py         # Arka plan güncelleme thread'i
    └── ui/
        ├── main_window.py    # Ana pencere
        ├── tray_icon.py      # Sistem tepsisi
        └── styles.py         # QSS koyu tema
```

---

## 🔒 Güvenlik & Gizlilik

- Uygulama **hiçbir veri toplamaz** ve **internete bağlanmaz** (DNS sorgusunun kendisi hariç)
- Tüm işlemler yerel makinenizde gerçekleşir
- Kaynak kodu tamamen açıktır — denetleyebilirsiniz

---

## 📜 Lisans

MIT License — bkz. [LICENSE](LICENSE)

---

## 🤝 Katkı

PR'lar ve issue'lar açıktır. Yeni domain eklemek veya özellik önermek için lütfen bir issue açın.
