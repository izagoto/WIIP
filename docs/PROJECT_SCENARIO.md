# Skenario Proyek: Evidentra Digital Forensics & Intelligence Platform

## Dokumen Skenario Eksekusi Proyek

| Properti | Nilai |
|---|---|
| **Nama Proyek** | Evidentra Digital Forensics & Intelligence Platform |
| **Kode Proyek** | Digifor Brimob |
| **Dokumen Sumber** | `Solution_Pack_Digifor_Brimob.pdf` |
| **Dokumen Spesifikasi** | `Spectek_Digital_Forensics_Intelligence_Module.pdf` |
| **Versi Dokumen** | 1.0 |
| **Tanggal** | 2026-08-05 |
| **Status** | Draft untuk Tim Cyber |

---

## 1. Gambaran Umum Skenario

Organisasi pengguna (Brimob) menjalankan kegiatan operasional yang kerap melibatkan pengumpulan dan penanganan data digital di lapangan, seperti data dari perangkat seluler, drone, media penyimpanan, serta berkas dan akun elektronik lainnya. Data digital bersifat mudah berubah (volatile) dan rentan rusak, terhapus, atau termodifikasi dari jarak jauh apabila tidak ditangani dengan prosedur dan peralatan yang tepat sejak dari lokasi kegiatan.

Keterbatasan kemampuan akuisisi dan analisis data di lapangan menyebabkan proses pemeriksaan harus dilakukan di pusat, sehingga memperlambat penyelesaian pekerjaan dan meningkatkan risiko terhadap keutuhan data. Oleh karena itu, diperlukan dukungan platform perangkat lunak forensik digital yang mampu melakukan akuisisi, pengamanan, penyimpanan, analisis, dan pengelolaan data digital secara cepat, aman, dan terjaga keutuhannya langsung dari lokasi kegiatan.

Solusi yang diusulkan adalah **Evidentra Platform** — platform perangkat lunak terpusat yang menyediakan modul akuisisi data, WhatsApp Intelligence, platform pengelolaan pekerjaan, manajemen data digital dengan verifikasi keutuhan SHA-256, dan modul Strategic Intelligence & Correlation untuk analisis keterkaitan entitas dan pemetaan konteks.

---

## 2. Dokumen Referensi

| Dokumen | Keterangan |
|---|---|
| `Solution_Pack_Digifor_Brimob.pdf` | Dokumen solusi lengkap (10 halaman) — berisi latar belakang, kebutuhan pengguna, solusi yang diusulkan, spesifikasi hardware, dan lisensi perangkat lunak |
| `Spectek_Digital_Forensics_Intelligence_Module.pdf` | Ekstrak spesifikasi teknis perangkat lunak (5 halaman) — berisi spesifikasi detail sub-modul d.5 hingga d.8 |

---

## 3. Cakupan Proyek

Proyek ini mencakup pengembangan **4 sub-modul** dengan **20 fitur** pada platform Evidentra:

| Sub-Modul | Kode | Jumlah Fitur | Status Pengembangan |
|---|---|---|---|
| WhatsApp Intelligence | d.5 | 4 | Kode awal sudah ada di `extractors/whatsapp_extractor/` |
| Tactical Operations & Case Platform | d.6 | 8 | Belum diimplementasi |
| Digital Evidence Management | d.7 | 8 | Belum diimplementasi |
| Strategic Intelligence & Correlation | d.8 | 4 | Belum diimplementasi |

### 3.1 Yang Di Luar Cakupan (Saat Ini)

- d.1 Cloud Data Acquisition & Analysis Software
- d.2 Mobile Data Acquisition & Analysis Software
- d.3 Drone Data Acquisition & Analysis Software
- Spesifikasi hardware (perangkat akuisisi, keamanan, infrastruktur lapangan)

---

## 4. Breakdown Fitur dan Tugas Detail

### 4.1 d.5 — WhatsApp Intelligence

Sub-modul berfokus pada parsing, validasi, pemetaan keterkaitan, dan analisis data percakapan serta interaksi WhatsApp.

| Kode | Nama Fitur | Deskripsi Spesifikasi Teknis | Tugas Teknis |
|---|---|---|---|
| d.5.1 | WhatsApp Data Acquisition | Pengambilan, validasi, dan penataan data percakapan serta kontak WhatsApp dari sumber yang kompatibel untuk mendukung proses analisis dan pengelolaan informasi. | Finalisasi ekstraksi kunci WhatsApp (`extract_keys_wa.py`), decrypt database (`decrypt-wa.py`), merge multi-DB SQLite (`merge_dbs_sqlite.py`), dan validasi data `msgstore.db` |
| d.5.2 | Communication Profile Analyzer | Menyajikan ringkasan pola komunikasi, termasuk kontak dominan, frekuensi interaksi, grup aktif, dan kecenderungan waktu komunikasi. | Bangun modul analisis profil: hitung kontak dominan, frekuensi interaksi, grup aktif, pola waktu komunikasi dari data WhatsApp yang sudah diekstrak |
| d.5.3 | AI Context Mapping | Membantu memetakan keterkaitan konteks percakapan berdasarkan topik, entitas, kata kunci, dan hubungan antardiskusi dengan dukungan AI. | Integrasikan NLP/LLM untuk pemetaan konteks percakapan — identifikasi topik, entitas, kata kunci, dan hubungan antar diskusi |
| d.5.4 | Search, Filter & Insight Reporting | Menyediakan pencarian, penyaringan, dan ringkasan hasil berdasarkan kontak, waktu, kata kunci, jenis konten, serta indikator aktivitas. | Bangun mesin pencarian dan filter (berdasarkan kontak, waktu, keyword, jenis konten) serta generate ringkasan insight |

**Catatan Arsitektur d.5:** Fokus pada ekstraksi/parsing database SQLite WhatsApp (`msgstore.db`), modul analisis profil interaksi, kluster topik NLP/LLM untuk pemetaan konteks, serta mesin indeks pencarian cepat.

---

### 4.2 d.6 — Tactical Operations & Case Platform

Sub-modul menangani manajemen alur kerja penyidikan/kasus, pembagian tugas personel, hierarki organisasi, kontrol akses (RBAC), serta pencatatan log audit.

| Kode | Nama Fitur | Deskripsi Spesifikasi Teknis | Tugas Teknis |
|---|---|---|---|
| d.6.1 | Case Registration | Pendaftaran kasus baru, pencatatan informasi awal, penetapan tingkat prioritas, unit penanggung jawab, serta perlindungan data deskripsi kasus. | Implementasi CRUD kasus dengan metadata: informasi awal, prioritas, unit penanggung jawab, perlindungan data deskripsi |
| d.6.2 | Investigation Dashboard | Dashboard visual untuk menampilkan ringkasan jumlah kasus, tingkat prioritas, beban tugas, progres penanganan, dan aktivitas sistem secara real-time. | Bangun dashboard visual dengan data real-time: ringkasan kasus, prioritas, beban tugas, progres penanganan |
| d.6.3 | Task Assignment Module | Pengelolaan tugas pemeriksaan, penugasan checklist kepada personel, penetapan tenggat waktu, serta pengaturan tingkat urgensi pekerjaan. | Implementasi pengelolaan tugas: penugasan checklist, tenggat waktu, tingkat urgensi |
| d.6.4 | Kanban Workflow Tracking | Papan kerja Kanban untuk memantau status tugas secara transparan melalui tahapan TODO, IN_PROGRESS, dan DONE. | Bangun papan kerja Kanban dengan status TODO → IN_PROGRESS → DONE |
| d.6.5 | Organizational Hierarchy Portal | Visualisasi struktur organisasi dan rantai koordinasi untuk mendukung pendelegasian wewenang, pembagian tanggung jawab, dan supervisi personel. | Implementasi visualisasi struktur organisasi dan rantai koordinasi |
| d.6.6 | Identity & Access Management | Autentikasi dan kontrol akses akun berbasis peran dan kewenangan (RBAC), termasuk verifikasi registrasi pengguna baru serta pengaturan hak akses setiap level. | Implementasi auth (JWT/OAuth) dan RBAC: registrasi pengguna, verifikasi, pengaturan hak akses per level |
| d.6.7 | System Audit & Logging | Pencatatan aktivitas pengguna dan perubahan data secara read-only untuk mendukung keterlacakan, evaluasi penggunaan, dan kebutuhan audit sistem. | Implementasi log audit read-only: catat semua aktivitas pengguna dan perubahan data |
| d.6.8 | Report Generation Engine | Penyusunan hasil analisis digital, kronologi kasus, daftar data pendukung, dan ringkasan kegiatan menjadi dokumen laporan berformat PDF. | Implementasi modul export laporan PDF otomatis |

**Catatan Arsitektur d.6:** Fokus pada Case Lifecycle Management, manajemen peran pengguna berbasis RBAC, papan Kanban interaktif, immutability log audit, dan modul export/reporting PDF otomatis.

---

### 4.3 d.7 — Digital Evidence Management

Sub-modul berfokus pada manajemen rantai pengawasan barang bukti (Chain of Custody), verifikasi integritas hash, registrasi metadata, dan pelacakan lokasi spasial.

| Kode | Nama Fitur | Deskripsi Spesifikasi Teknis | Tugas Teknis |
|---|---|---|---|
| d.7.1 | Central Evidence Repository | Repository terpusat untuk menyimpan, mencari, mengarsipkan, dan mengelompokkan seluruh data barang bukti berdasarkan kasus dan kategori. | Implementasi repository terpusat dengan CRUD pencarian, arsip, dan pengelompokan berdasarkan kasus dan kategori |
| d.7.2 | Evidence Registration Module | Pencatatan metadata barang bukti, meliputi jenis, merek, IMEI, nomor seri, kapasitas, foto awal, kondisi penerimaan, serta koordinat lokasi perolehan. | Implementasi pencatatan metadata barang bukti lengkap |
| d.7.3 | Evidence Custody & Transfer Tracking | Pelacakan riwayat penguasaan dan perpindahan barang bukti (Chain of Custody), mencakup pemegang aktif, waktu serah terima, tujuan pemindahan, status penerimaan, serta catatan verifikasi pada setiap tahapan. | Implementasi pelacakan riwayat penguasaan dan perpindahan barang bukti |
| d.7.4 | Evidence Transfer Approval | Mekanisme persetujuan serah terima barang bukti yang memerlukan konfirmasi dari pihak pengirim dan penerima sebelum perubahan pemegang dicatat oleh sistem. | Implementasi mekanisme persetujuan serah terima dengan konfirmasi dua pihak |
| d.7.5 | Evidence Integrity Verification | Verifikasi integritas data barang bukti digital melalui perhitungan dan pencatatan nilai hash SHA-256 untuk mendeteksi perubahan terhadap data. | Implementasi perhitungan dan pencatatan hash SHA-256 otomatis |
| d.7.6 | Asset Vault Registry | Pengelompokan barang bukti berdasarkan lokasi penyimpanan dan kategori, seperti perangkat, seluler, dokumen, dan media, untuk memudahkan pengamanan serta pencarian. | Implementasi pengelompokan barang bukti berdasarkan lokasi dan kategori |
| d.7.7 | Custody Report Generator | Penyusunan riwayat serah terima barang bukti menjadi dokumen Berita Acara Serah Terima (BAST), termasuk dukungan pemilihan beberapa barang bukti dalam satu transaksi. | Implementasi generator laporan BAST dengan dukungan multi-barang bukti |
| d.7.8 | Geospatial Evidence Tracking | Pencatatan dan visualisasi koordinat lokasi perolehan barang bukti untuk mendukung penelusuran lokasi serta keterkaitan data secara spasial. | Implementasi pencatatan dan visualisasi koordinat GPS/GIS |

**Catatan Arsitektur d.7:** Menjaga kepatuhan aturan standar forensik digital (Chain of Custody), kueri/pencatatan hash SHA-256 otomatis, alur persetujuan serah terima (BAST), dan pemetaan spasial GPS/GIS.

---

### 4.4 d.8 — Strategic Intelligence & Correlation

Sub-modul berfokus pada korelasi dokumen tingkat lanjut (Named Entity Recognition), analisis hubungan antar entitas (Graph Analytics), serta inspeksi statis berkas APK.

| Kode | Nama Fitur | Deskripsi Spesifikasi Teknis | Tugas Teknis |
|---|---|---|---|
| d.8.1 | Neural Document Correlation | Pemrosesan dokumen hasil akuisisi dalam format CSV dan PDF untuk mengidentifikasi entitas penting, seperti nama, objek, lokasi, dan tanggal, secara otomatis (Named Entity Recognition). | Implementasi NER untuk dokumen CSV dan PDF — identifikasi entitas otomatis (nama, objek, lokasi, tanggal) |
| d.8.2 | Relationship Link Analysis | Analisis frekuensi interaksi dan visualisasi keterkaitan antar entitas atau kontak berdasarkan data komunikasi yang tersedia (Graph Analytics). | Implementasi analisis graf hubungan dan visualisasi keterkaitan antar entitas |
| d.8.3 | APK Static Analysis Inspector | Analisis statis berkas APK untuk meninjau Android Manifest, izin aplikasi, komponen, sertifikat, serta indikator ancaman pada berkas DEX. | Implementasi parser/decompiler APK statis: Android Manifest, izin, komponen, sertifikat, indikator ancaman DEX |
| d.8.4 | Advanced Analysis Dashboard | Dashboard analitik untuk menampilkan metrik pemrosesan data, jumlah berkas yang dianalisis, status pekerjaan, hasil korelasi, dan latensi layanan. | Implementasi dashboard analitik dengan metrik pemrosesan, status pekerjaan, hasil korelasi, dan latensi |

**Catatan Arsitektur d.8:** Pemrosesan AI/ML untuk ekstraksi entitas (NER), pemetaan graf hubungan (Network Graph), parser/decompiler analisis statis APK, serta pemantauan latensi backend API.

---

## 5. Rencana Sprint

### Asumsi Tim

| Parameter | Nilai |
|---|---|
| Jumlah Pengembang | 3–5 orang |
| Durasi Sprint | 2 minggu per sprint |
| Total Sprint | 6 sprint |
| Estimasi Total Durasi | ~12 minggu (~3 bulan) |
| Peran | Backend Engineer, ML/AI Specialist, Frontend Engineer (opsional jika dashboard web), QA Engineer |

---

### Sprint 1 — Foundation & WhatsApp Intelligence Completion

**Durasi:** 2 minggu
**Tujuan:** Menyelesaikan d.5 WhatsApp Intelligence dan menyiapkan fondasi arsitektur platform.

| ID | Fitur | Deskripsi Tugas | Prioritas |
|---|---|---|---|
| T-1.1 | d.5.1 WhatsApp Data Acquisition | Finalisasi `extract_keys_wa.py`, `decrypt-wa.py`, `merge_dbs_sqlite.py` — pastikan parsing `msgstore.db` SQLite berjalan lengkap dengan validasi data | High |
| T-1.2 | d.5.2 Communication Profile Analyzer | Bangun modul analisis profil komunikasi: hitung kontak dominan, frekuensi interaksi, grup aktif, pola waktu komunikasi dari data WhatsApp yang sudah diekstrak | High |
| T-1.3 | d.5.3 AI Context Mapping | Integrasikan NLP/LLM untuk pemetaan konteks percakapan — identifikasi topik, entitas, kata kunci, dan hubungan antar diskusi | Medium |
| T-1.4 | d.5.4 Search, Filter & Insight Reporting | Bangun mesin pencarian dan filter (berdasarkan kontak, waktu, keyword, jenis konten) serta generate ringkasan insight | Medium |
| T-1.5 | Database Schema Design | Rancang schema database PostgreSQL/SQLite untuk menyimpan hasil ekstraksi WhatsApp, metadata kasus, dan bukti digital | High |
| T-1.6 | Project Scaffold | Buat struktur proyek modular: `core/`, `modules/d.5/`, `modules/d.6/`, `modules/d.7/`, `modules/d.8/`, `api/`, `models/` | High |

**Deliverable Sprint 1:**
- Kode WhatsApp extractor yang terstruktur dan terintegrasi ke dalam modular project scaffold
- Schema database untuk WhatsApp data dan metadata
- Fitur pencarian, filter, dan insight reporting untuk data WhatsApp

---

### Sprint 2 — Tactical Operations & Case Platform (Part 1)

**Durasi:** 2 minggu
**Tujuan:** Membangun inti manajemen kasus dan operasi penyidikan.

| ID | Fitur | Deskripsi Tugas | Prioritas |
|---|---|---|---|
| T-2.1 | d.6.1 Case Registration | Implementasi pendaftaran kasus baru dengan metadata: informasi awal, prioritas, unit penanggung jawab, perlindungan data deskripsi | High |
| T-2.2 | d.6.2 Investigation Dashboard | Dashboard visual untuk menampilkan ringkasan jumlah kasus, tingkat prioritas, beban tugas, progres penanganan secara real-time | High |
| T-2.3 | d.6.3 Task Assignment Module | Pengelolaan tugas pemeriksaan: penugasan checklist ke personel, tenggat waktu, tingkat urgensi | High |
| T-2.4 | d.6.4 Kanban Workflow Tracking | Papan kerja Kanban dengan status TODO → IN_PROGRESS → DONE, transparan untuk tim | High |
| T-2.5 | API Layer | Bangun REST API (FastAPI/Flask) untuk semua endpoint d.6 — case CRUD, task CRUD, dashboard data | High |
| T-2.6 | Authentication Scaffold | Siapkan struktur auth (JWT/OAuth) sebagai fondasi untuk RBAC di Sprint 3 | High |

**Deliverable Sprint 2:**
- REST API untuk manajemen kasus dan tugas
- Dashboard investigasi dengan data real-time
- Papan Kanban untuk tracking status tugas
- Auth scaffold untuk RBAC

---

### Sprint 3 — Tactical Operations (Part 2) + Evidence Management (Part 1)

**Durasi:** 2 minggu
**Tujuan:** Menyelesaikan d.6 dan memulai d.7.

| ID | Fitur | Deskripsi Tugas | Prioritas |
|---|---|---|---|
| T-3.1 | d.6.5 Organizational Hierarchy Portal | Visualisasi struktur organisasi dan rantai koordinasi untuk pendelegasian wewenang | Medium |
| T-3.2 | d.6.6 Identity & Access Management (RBAC) | Autentikasi dan kontrol akses berbasis peran: verifikasi registrasi pengguna baru, pengaturan hak akses per level | High |
| T-3.3 | d.6.7 System Audit & Logging | Pencatatan aktivitas pengguna dan perubahan data secara read-only untuk audit trail | High |
| T-3.4 | d.6.8 Report Generation Engine | Implementasi modul export laporan PDF otomatis: hasil analisis, kronologi kasus, daftar data pendukung | Medium |
| T-3.5 | d.7.1 Central Evidence Repository | Implementasi repository terpusat dengan CRUD pencarian, arsip, dan pengelompokan berdasarkan kasus dan kategori | High |
| T-3.6 | d.7.2 Evidence Registration Module | Implementasi pencatatan metadata barang bukti lengkap (jenis, merek, IMEI, nomor seri, kapasitas, foto awal, kondisi penerimaan, koordinat lokasi) | High |

**Deliverable Sprint 3:**
- RBAC lengkap dengan hierarki organisasi
- Audit log read-only
- Laporan PDF otomatis
- Central Evidence Repository dan Evidence Registration Module

---

### Sprint 4 — Digital Evidence Management (Part 2)

**Durasi:** 2 minggu
**Tujuan:** Menyelesaikan d.7 dengan fokus pada Chain of Custody dan integritas bukti.

| ID | Fitur | Deskripsi Tugas | Prioritas |
|---|---|---|---|
| T-4.1 | d.7.3 Evidence Custody & Transfer Tracking | Implementasi pelacakan riwayat penguasaan dan perpindahan barang bukti: pemegang aktif, waktu serah terima, tujuan pemindahan, status penerimaan | High |
| T-4.2 | d.7.4 Evidence Transfer Approval | Implementasi mekanisme persetujuan serah terima dengan konfirmasi dua pihak (pengirim dan penerima) | High |
| T-4.3 | d.7.5 Evidence Integrity Verification | Implementasi perhitungan dan pencatatan hash SHA-256 otomatis untuk deteksi perubahan data | High |
| T-4.4 | d.7.6 Asset Vault Registry | Implementasi pengelompokan barang bukti berdasarkan lokasi penyimpanan dan kategori (perangkat, seluler, dokumen, media) | Medium |
| T-4.5 | d.7.7 Custody Report Generator | Implementasi generator laporan BAST (Berita Acara Serah Terima) dengan dukungan multi-barang bukti | Medium |
| T-4.6 | d.7.8 Geospatial Evidence Tracking | Implementasi pencatatan dan visualisasi koordinat GPS/GIS untuk lokasi perolehan barang bukti | Medium |

**Deliverable Sprint 4:**
- Chain of Custody tracking lengkap dengan approval workflow
- SHA-256 integrity verification otomatis
- BAST report generator
- Geospatial evidence tracking dengan peta visual

---

### Sprint 5 — Strategic Intelligence & Correlation (Part 1)

**Durasi:** 2 minggu
**Tujuan:** Membangun modul kecerdasan strategis dan korelasi data.

| ID | Fitur | Deskripsi Tugas | Prioritas |
|---|---|---|---|
| T-5.1 | d.8.1 Neural Document Correlation (NER) | Implementasi NER untuk dokumen CSV dan PDF — identifikasi entitas otomatis (nama, objek, lokasi, tanggal) | High |
| T-5.2 | d.8.2 Relationship Link Analysis | Implementasi analisis graf hubungan dan visualisasi keterkaitan antar entitas berdasarkan data komunikasi | High |
| T-5.3 | d.8.3 APK Static Analysis Inspector | Implementasi parser/decompiler APK statis: Android Manifest, izin aplikasi, komponen, sertifikat, indikator ancaman DEX | Medium |
| T-5.4 | ML/AI Pipeline Infrastructure | Siapkan pipeline inference untuk NER dan graph analytics — model loading, preprocessing, result caching | High |

**Deliverable Sprint 5:**
- NER engine untuk dokumen CSV/PDF
- Relationship graph analytics dengan visualisasi
- APK static analysis inspector
- ML/AI pipeline infrastructure

---

### Sprint 6 — Strategic Intelligence (Part 2) + Integration & Testing

**Durasi:** 2 minggu
**Tujuan:** Menyelesaikan d.8 dan mengintegrasikan seluruh modul.

| ID | Fitur | Deskripsi Tugas | Prioritas |
|---|---|---|---|
| T-6.1 | d.8.4 Advanced Analysis Dashboard | Implementasi dashboard analitik dengan metrik pemrosesan data, jumlah berkas dianalisis, status pekerjaan, hasil korelasi, dan latensi layanan | High |
| T-6.2 | Cross-Module Integration | Hubungkan seluruh modul: WhatsApp data → Case → Evidence → Intelligence — pastikan data mengalir antar sub-modul | High |
| T-6.3 | End-to-End Testing | Pengujian integrasi penuh: dari akuisisi WhatsApp → pembuatan kasus → registrasi bukti → analisis intelligence → laporan PDF | High |
| T-6.4 | Performance Optimization | Optimasi query database, indeks pencarian, caching untuk dashboard real-time | Medium |
| T-6.5 | Documentation & API Docs | Dokumentasi teknis lengkap untuk semua modul, endpoint API, dan panduan penggunaan | Medium |

**Deliverable Sprint 6:**
- Advanced Analysis Dashboard
- Integrasi lintas modul (end-to-end)
- Hasil pengujian integrasi
- Dokumentasi teknis dan API docs

---

## 6. Dependency Map

```
Sprint 1 (d.5 + Foundation)
  │
  ├──► Sprint 2 (d.6.1–d.6.4 + API + Auth)
  │       │
  │       ├──► Sprint 3 (d.6.5–d.6.8 + d.7.1–d.7.2)
  │       │       │
  │       │       └──► Sprint 4 (d.7.3–d.7.8)
  │       │               │
  │       │               └──► Sprint 5 (d.8.1–d.8.3 + ML Pipeline)
  │       │                       │
  │       │                       └──► Sprint 6 (d.8.4 + Integration + Testing)
  │       │
  │       └── d.6.6 (RBAC) diperlukan oleh semua modul selanjutnya
  │
  └── d.5 data menjadi input untuk d.8.1 (NER) dan d.8.2 (Graph Analysis)
```

### Dependency Kritis

| Dependency | Keterangan |
|---|---|
| Sprint 1 → Sprint 2 | Database schema dan project scaffold harus selesai sebelum API dibangun |
| Sprint 2 → Sprint 3 | Auth scaffold (Sprint 2) harus selesai sebelum RBAC diimplementasikan (Sprint 3) |
| d.6.6 (RBAC) | Harus selesai sebelum d.6.7 (Audit Log) karena audit log bergantung pada identitas pengguna yang terautentikasi |
| d.7.1–d.7.2 → d.7.3–d.7.8 | Repository dan registrasi bukti harus ada sebelum tracking dan pelaporan custody |
| d.5 → d.8.1, d.8.2 | NER dan graph analytics bergantung pada data WhatsApp yang terstruktur |
| Sprint 5 → Sprint 6 | ML pipeline (Sprint 5) harus ada sebelum dashboard analitik (Sprint 6) dapat menampilkan hasil korelasi |

---

## 7. Risk Assessment

| Risiko | Kemungkinan | Dampak | Mitigasi |
|---|---|---|---|
| WhatsApp extractor yang ada memerlukan refactor besar | Medium | High | Mulai Sprint 1 dengan audit kode existing; buat branch untuk refactor; pertahankan kompatibilitas backward |
| NER/ML model tidak akurat untuk konteks Bahasa Indonesia | Medium | Medium | Gunakan pre-trained model yang mendukung Bahasa Indonesia; siapkan dataset training lokal; iterasi di Sprint 5–6 |
| SHA-256 integrity verification memerlukan performa tinggi untuk dataset besar | Medium | High | Implementasi hashing asinkron dan batch processing; gunakan multi-threading |
| RBAC implementation salah menyebabkan celah keamanan | Low | Critical | Review oleh tim keamanan; gunakan library auth yang sudah teruji (mis. FastAPI Users, OAuth2) |
| Integrasi lintas modul di Sprint 6 menunjukkan incompatibility | Medium | High | Lakukan integration testing bertahap mulai Sprint 3; gunakan contract testing antar modul |
| Timeline terdorong karena kompleksitas d.7 (Chain of Custody) | Medium | Medium | Prioritaskan fitur kritis d.7 (d.7.3–d.7.5) di Sprint 4; fitur non-kritis (d.7.6–d.7.8) bisa ditunda jika perlu |

---

## 8. Definition of Done (DoD)

Setiap tugas/fitur dianggap selesai jika:

1. **Kode implementasi** sudah ditulis dan mengikuti konvensi proyek
2. **Unit tests** sudah ditulis dan passing untuk fitur tersebut
3. **Integration tests** sudah passing (untuk fitur yang berinteraksi dengan modul lain)
4. **Database migration** sudah tersedia (jika ada perubahan schema)
5. **API documentation** sudah diperbarui (Swagger/OpenAPI jika menggunakan FastAPI)
6. **Code review** sudah dilakukan oleh minimal 1 anggota tim lain
7. **No critical or high severity bugs** yang terbuka terkait fitur tersebut

---

## 9. Struktur Proyek yang Diharapkan (Target Akhir)

```
brimob_forensiq/
├── docs/
│   ├── Solution_Pack_Digifor_Brimob.pdf
│   ├── Spectek_Digital_Forensics_Intelligence_Module.pdf
│   └── PROJECT_SCENARIO.md          ← dokumen ini
├── extractors/
│   └── whatsapp_extractor/          ← existing (d.5.1)
│       ├── __init__.py
│       ├── cmd.py
│       ├── decrypt-wa.py
│       ├── extract-keys.py
│       ├── extract_keys_wa.py
│       ├── get_number_wa.py
│       ├── merge_dbs_sqlite.py
│       ├── whatsapp_backup_setup.py
│       ├── backup/
│       ├── db_whatsapp/
│       ├── pull/
│       └── proto/
├── core/                            ← NEW: shared utilities, database connection, config
├── modules/
│   ├── d5_whatsapp/                 ← NEW: WhatsApp Intelligence
│   ├── d6_operations/               ← NEW: Tactical Operations & Case Platform
│   ├── d7_evidence/                 ← NEW: Digital Evidence Management
│   └── d8_intelligence/             ← NEW: Strategic Intelligence & Correlation
├── api/                             ← NEW: REST API layer
├── models/                          ← NEW: database models / ORM
├── data/
│   ├── raw_evidence/
│   ├── processed/
│   └── exports/
├── tests/                           ← NEW: unit and integration tests
├── requirements.txt                 ← semua dependensi Python
├── pyrightconfig.json
└── README.md                        ← NEW: project documentation
```

---

## 10. Catatan Pelaksanaan

- Dokumen ini adalah **living document** dan akan diperbarui seiring perkembangan proyek.
- Setiap sprint harus memiliki **review meeting** di akhir sprint untuk mengevaluasi deliverable dan menyesuaikan rencana.
- Perubahan cakupan (scope creep) harus disetujui oleh lead project sebelum dimasukkan ke sprint berikutnya.
- Dokumen ini bersumber dari `Spectek_Digital_Forensics_Intelligence_Module.pdf` (ekstrak spesifikasi) dan `Solution_Pack_Digifor_Brimob.pdf` (dokumen solusi lengkap).
