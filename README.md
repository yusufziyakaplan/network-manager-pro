# ⚡ Network Manager Pro v2

WiFi ve Ethernet bağlantısını aynı anda yönet. Tarayıcıları WiFi'den, diğer tüm programları Ethernet'ten internete çıkar.

---

## 🚀 Ne İşe Yarar?

Aynı anda hem WiFi hem Ethernet bağlıyken:
- **Chrome / Firefox** → WiFi üzerinden internete çıkar
- **Diğer tüm programlar** → Ethernet üzerinden internete çıkar

Bunu bir **yerel proxy** (port 8888) kurarak sağlar. Tarayıcı trafiği proxy üzerinden WiFi arayüzüne yönlendirilir.

---

## 🖥️ Ekran Görüntüsü

> Program açıldığında UAC ile yönetici izni ister, ardından arayüz gelir.
<img width="733" height="822" alt="1" src="https://github.com/user-attachments/assets/a6e96c16-b552-4bf0-8482-3a2291a2b89c" />

---

## ⚙️ Özellikler

- ✅ Chrome ve Firefox desteği (ayrı ayrı veya birlikte)
- ✅ Tarayıcı kısayollarını otomatik güncelleme (her açılışta WiFi kullanır)
- ✅ Firefox profil proxy ayarı (`user.js` ile)
- ✅ Ethernet metric otomatik yönetimi
- ✅ Sistem durdurulunca Ethernet IP'si otomatik yenilenir
- ✅ Windows başlangıcında otomatik başlatma
- ✅ Sistem tepsisinde (system tray) çalışma
- ✅ Ayarlar JSON olarak kaydedilir

---

## 📦 Kurulum

### Hazır EXE (Önerilen)
[Releases](https://github.com/yusufziyakaplan/network-manager-pro/releases) sayfasından son sürümü indir, çift tıkla çalıştır.

> ⚠️ Program yönetici (admin) izni gerektirir, UAC penceresi açılır.

### Python ile Çalıştırma

```bash
pip install -r requirements.txt
python network_manager_pro2.py
```

**Gereksinimler:**
```
psutil
pystray
Pillow
pywin32
```

---

## 🛠️ EXE Derleme

```bash
build_v2.bat
```

> Python 3.13 64-bit gereklidir.

---

## 📋 Kullanım

1. Programı yönetici olarak çalıştır
2. **WiFi** arayüzünü seç (tarayıcılar bu ağdan çıkacak)
3. **Ethernet** arayüzünü seç (diğer programlar bu ağdan çıkacak)
4. Hangi tarayıcıları WiFi'den çalıştırmak istediğini seç
5. **BAŞLAT** butonuna tıkla
6. Durdurmak için **DURDUR** — Ethernet otomatik eski haline gelir

---

## 👨‍💻 Geliştirici

**Yusuf Ziya Kaplan**
🔗 [github.com/yusufziyakaplan](https://github.com/yusufziyakaplan?tab=repositories)

---

## 📄 Lisans

MIT License
