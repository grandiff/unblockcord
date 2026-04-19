# 🗺️ UnblockCord — Roadmap

## ✅ Tamamlananlar

| Sürüm | Özellik |
|---|---|
| v1.0.0 | DNS bypass (Cloudflare DoH + Google DoH + nslookup fallback) |
| v1.0.0 | SNI/DPI bypass — TLS fragmentasyon proxy'si |
| v1.0.0 | Discord güncelleme sorunu çözüldü |
| v1.0.0 | Port fallback (127.0.0.1 – 127.0.0.10 otomatik) |
| v1.0.0 | Sistem tepsisi, otomatik daemon, hosts yönetimi |
| v1.1.0 | Bağlantı izleme (Watchdog) — 60sn'de bir otomatik test |
| v1.1.0 | Windows autostart — kayıt defteri entegrasyonu |
| v1.1.0 | Masaüstü bildirimleri — bağlantı kopma/düzelme |
| v1.1.0 | Bağlantı testi düzeltmesi — gerçek Cloudflare IP'si ile test |

---

## 🚧 v1.2.0 — Arayüz Yenileme + Ayarlar Paneli *(Sıradaki)*

### 🔴 Öncelikli

- [ ] **Ayarlar Butonu (⚙️)** — tüm ayarları tek panelde topla
  - Güncelleme aralığı
  - Auto-restart Discord toggle
  - Windows autostart toggle
  - Gelecekteki tüm ayarlar buraya

- [ ] **Tam Arayüz Redesign**
  - Kontrol çubuğundaki yazı taşmaları düzeltilecek
  - Butonlar icon-only + tooltip formatına alınacak
  - Minimum pencere genişliği artırılacak (920px)
  - Responsive layout — küçültünce elementler kaymayacak
  - Header, tablo ve log paneli yeniden düzenlenecek

---

## 📅 v1.3.0 — Özellik Paketi

### 🌐 Ağ & Bypass

- [ ] **FRAG_SIZE UI ayarı** — TLS parça boyutu seçilebilsin (2 / 4 / 8 byte)
- [ ] **Bağlantı geçmişi grafiği** — Son 24 saatin ping/uptime grafiği
- [ ] **Özel domain ekleme** — Kullanıcı kendi listesini yönetebilsin
- [ ] **Proxy port seçimi** — Port 443 dışı alternatif port desteği

### 🖥️ Kullanıcı Deneyimi

- [ ] **İlk çalıştırma sihirbazı** — Yeni kullanıcılar için 3 adımlı kurulum rehberi
- [ ] **Dil desteği** — Türkçe / İngilizce
- [ ] **Tema seçeneği** — Koyu (mevcut) / Açık tema
- [ ] **Log geçmişi** — Uygulama kapanınca log sıfırlanmasın

### 🔧 Güvenilirlik

- [ ] **Watchdog aralığı ayarlanabilsin** — 30s / 60s / 120s
- [ ] **Discord crash tespiti** — Discord kapanınca opsiyonel otomatik yeniden başlatma
- [ ] **Hata günlüğü** — Kritik hatalar `error.log` dosyasına kaydedilsin
- [ ] **Güncel sürüm kontrolü** — GitHub Releases'ten yeni sürüm bildirimi

### 🚀 Altyapı

- [ ] **GitHub Actions** — Her push'ta otomatik build + Release (CI/CD)
- [ ] **SHA256 checksum** — Her release'e exe hash'i eklensin
- [ ] **Installer** — NSIS veya Inno Setup ile kurulum sihirbazı

---

> Katkı sağlamak için bir **Issue** açın veya **Pull Request** gönderin.
