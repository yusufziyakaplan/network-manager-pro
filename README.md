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
https://github.com/yusufziyakaplan/network-manager-pro/issues/1#issue-4389749610

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
- ✅ **[YENİ]** ipeaklwf.sys sürücüsü devre dışı bırakma (BSOD / ağ çökmesi koruması)
- ✅ **[YENİ]** Tek tıkla tam ağ sıfırlama (Winsock, IP, DNS, Proxy, Firewall, Adaptörler)

---

## 🛡️ Yeni: Sürücü & Ağ Araçları

### ipeaklwf.sys Devre Dışı Bırakma
Intel Killer ağ kartlarında bulunan `ipeaklwf.sys` sürücüsü ağ çökmelerine ve mavi ekrana (BSOD) yol açabilir. Program içinden tek tıkla devre dışı bırakılabilir veya tekrar etkinleştirilebilir.

### Ağ Sıfırlama
PC'nin ağ ayarları karıştığında tek butonla her şeyi sıfırlar:
- Winsock kataloğu sıfırlanır
- IP / IPv6 yığını sıfırlanır
- DNS önbelleği temizlenir
- ARP önbelleği temizlenir
- WinHTTP ve sistem proxy'si temizlenir
- Windows Firewall varsayılana döndürülür
- Tüm ağ adaptörleri yeniden başlatılır

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
7. **[YENİ]** Ağ sorunu yaşıyorsan → **Ağ Ayarlarını Sıfırla** butonunu kullan
8. **[YENİ]** BSOD / ağ çökmesi yaşıyorsan → **ipeaklwf.sys Devre Dışı Bırak** butonunu kullan

---

## 👨‍💻 Geliştirici

**Yusuf Ziya Kaplan**
🔗 [github.com/yusufziyakaplan](https://github.com/yusufziyakaplan?tab=repositories)

---

## 📄 Lisans

MIT License
