# WIIP (WhatsApp Intelligence & Investigation Platform)

WIIP adalah sebuah *Platform* Intelijen Investigasi yang mengubah bukti digital yang terfragmentasi (terpisah-pisah) menjadi sebuah ekosistem investigasi yang saling terhubung.

Alat forensik digital saat ini memang sangat efektif untuk mengekstrak barang bukti dari perangkat seluler. Namun, para investigator (penyidik) masih harus menghabiskan banyak waktu secara manual untuk mengkorelasikan percakapan, merekonstruksi linimasa (*timeline*), mengidentifikasi hubungan, dan memahami konteks di balik sebuah insiden.

Setiap pesan, individu, file media, lokasi, stempel waktu (*timestamp*), perangkat, dan peristiwa komunikasi akan diubah menjadi bagian dari satu grafik investigasi tunggal. Hal ini memungkinkan para penyidik untuk tidak hanya memahami "apa yang terjadi", tetapi juga melihat secara jelas bagaimana setiap kepingan bukti saling terhubung satu sama lain.

**Tagline**: *Melampaui Forensik WhatsApp Biasa. Dibangun Khusus untuk Intelijen Investigasi.*

---

## 🛠️ Library & Tools

Proyek ini dibangun menggunakan kumpulan *tools* dan *library* berikut:
- **[Python 3.8+](https://www.python.org/downloads/)**: Bahasa pemrograman utama.
- **[uiautomator2](https://github.com/openatx/uiautomator2)**: Library Python untuk otomatisasi UI Android (mengeklik layar, *swipe*, dsb).
- **[WEditor](https://github.com/alibaba/web-editor)**: Tool wajib bagi pengembang untuk menginspeksi UI (*UI Inspector*) guna mendapatkan `resource-id` atau `xpath` di layar Android.
- **[ADB (Android Debug Bridge)](https://developer.android.com/studio/command-line/adb)**: Tool command-line untuk berkomunikasi dengan perangkat Android.
- **SQLite3**: Untuk pemrosesan dan ekstraksi data dari database `.db`.

---

## ⚙️ Instalasi

Ikuti langkah-langkah di bawah ini untuk menyiapkan *environment* proyek WIIP di komputer Anda.

### 1. Git Clone
Unduh proyek ini ke komputer lokal Anda:
```bash
git clone <URL_REPOSITORY_ANDA>
cd WIIP
```

### 2. Buat Virtual Environment (Opsional tapi disarankan)
Agar *library* tidak bentrok dengan *project* Python Anda yang lain:
```bash
python -m venv .venv

# Aktivasi untuk Mac/Linux:
source .venv/bin/activate

# Aktivasi untuk Windows:
.venv\Scripts\activate
```

### 3. Instalasi Dependencies & Tools Tambahan
Instal semua *library* Python yang dibutuhkan, termasuk `uiautomator2` dan `weditor`:
```bash
# Instal UI Automator 2
pip install uiautomator2

# Instal WEditor (Untuk inspeksi elemen UI layar Android)
pip install weditor

# Jika backend API digunakan, jalankan juga:
pip install -r backend/requirements.txt
```
*(Catatan: Setelah menginstal weditor, Anda bisa menjalankannya di terminal dengan perintah `python -m weditor` atau `weditor` untuk membuka antarmuka UI inspector di browser).*

### 4. Instalasi & Setup ADB
Skrip ini wajib menggunakan ADB agar bisa mengontrol HP Android. Anda bisa mengunduh ADB resmi langsung dari Google:
- **Windows / Mac / Linux (Resmi)**: [Unduh SDK Platform-Tools](https://developer.android.com/studio/releases/platform-tools)
- **Instruksi Ekstrak Windows**: Setelah diunduh, ekstrak folder tersebut dan [tambahkan ke Environment Variables (PATH) komputer Anda](https://www.xda-developers.com/install-adb-windows-macos-linux/#how-to-set-up-adb-on-windows).

**Alternatif Instalasi Instan:**
- **Mac (Homebrew)**: `brew install android-platform-tools`
- **Linux (Ubuntu/Debian)**: `sudo apt-get install android-tools-adb`

**Persiapan di HP Android Anda:**
1. Masuk ke **Settings** > **About Phone**, ketuk **Build Number** 7x.
2. Masuk ke **Developer Options** (Opsi Pengembang).
3. Aktifkan **USB Debugging**.
4. Colokkan HP ke PC, lalu jalankan `adb devices` di terminal. Pastikan status HP Anda terdeteksi (muncul tulisan `device`).

---

## 🚀 Quick Start

Setelah semua terinstal dan HP terhubung dengan PC dalam mode USB Debugging, Anda bisa langsung menjalankan ekstraksi otomatis:

```bash
python extractors/whatsapp_extractor/whatsapp_backup_setup.py
```

**Alur Otomatisasi (Skrip akan jalan sendiri):**
1. Skrip akan menutup paksa WhatsApp yang sedang terbuka (agar aman).
2. Membuka WhatsApp dan masuk ke menu *End-to-End Encryption*.
3. Jika *key* belum ada, skrip akan mengaktifkannya dan menyimpan *key* tersebut ke `extractors/whatsapp_extractor/pull/<serial_number>_key.txt`.
4. Skrip akan menekan tombol **Backup Now** dan menunggu hingga selesai.
5. Secara otomatis menarik (*pull*) `msgstore.db.crypt15` dan `wa.db.crypt15` ke PC.
6. Mendekripsi file tersebut menjadi *database* mentah SQLite yang bisa langsung Anda baca, disimpan di:
   `extractors/whatsapp_extractor/db_whatsapp/<serial_number>/`
7. Terakhir, skrip akan membersihkan layar HP Anda (*Recent Apps*).
