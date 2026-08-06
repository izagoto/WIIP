# Sistem Scenario — Evidentra Digital Forensics & Intelligence Platform

## Versi Dokumen

| Properti | Nilai |
|---|---|
| **Versi** | 1.0 |
| **Tanggal** | 2026-08-05 |
| **Status** | Draft |
| **Referensi** | `PROJECT_SCENARIO.md`, `ARCHITECTURE.md`, `DATABASE_SCHEMA.md` |

---

## 1. Gambaran Sistem Secara Keseluruhan

Evidentra adalah platform perangkat lunak berbasis web yang berjalan pada **Integrated Mobile Digital Data Laboratory** — laboratorium digital bergerak untuk operasi Brimob. Sistem ini mengintegrasikan empat sub-modul (d.5 WhatsApp Intelligence, d.6 Tactical Operations, d.7 Digital Evidence Management, d.8 Strategic Intelligence) dalam satu platform terpusat berbasis FastAPI + React/Vue.

User dapat mengakses sistem melalui:
1. **Web Browser** (frontend React/Vue + REST API)
2. **Mobile Device** (WhatsApp extraction via ADB/uiautomator2)
3. **CLI** (WhatsApp extractor untuk offline extraction)

---

## 2. Aktor dan Role

| Aktor | Role | Deskripsi |
|---|---|---|
| **Administrator** | Admin | Mengelola pengguna, role, dan konfigurasi sistem |
| **Investigator** | Investigator | Petugas lapangan yang mendaftarkan kasus, mengakuisisi bukti, dan menganalisis data |
| **Supervisor** | Viewer/Admin | Supervisor yang memantau progres dan menerima laporan |
| **System** | System | Komponen otomatis (Celery worker, scheduler) |
| **Device** | Device | Perangkat Android/iOS untuk akuisisi data WhatsApp |

---

## 3. Use Case Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     SYSTEM OVERVIEW                          │
│                                                              │
│  [Device Akuisisi]                                           │
│     WhatsApp Backup                                          │
│         │                                                    │
│         ▼                                                    │
│  [d.5 WhatsApp Intelligence]                                │
│  Extract → Analyze → Profile → Context Mapping              │
│         │                                                    │
│         ▼                                                    │
│  [d.6 Tactical Operations]                                  │
│  Register Case → Assign Task → Track Kanban                 │
│         │                                                    │
│         ▼                                                    │
│  [d.7 Digital Evidence Management]                          │
│  Register Evidence → Custody Tracking → SHA-256 Verify    │
│         │                                                    │
│         ▼                                                    │
│  [d.8 Strategic Intelligence]                               │
│  NER → Graph Analysis → APK Analysis → Dashboard             │
│         │                                                    │
│         ▼                                                    │
│  [Reporting & Export]                                       │
│  PDF Reports (Laporan Kasus, BAST, Intelligence)            │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. Skenario End-to-End (Scenario Flow)

Berikut adalah skenario penggunaan sistem yang menggambarkan alur kerja utama secara keseluruhan.

### Skenario: Investigator Menyelidiki Kasus dengan Bukti Digital WhatsApp

#### Aktor: Investigator (role: Investigator)

#### Premis
Seorang investigator menerima ponsel saklar dari lapangan yang berisi data WhatsApp terkait kasus penyelidikan. Investigator harus memindai bukti WhatsApp, mendaftarkan kasus, mengelola bukti, menganalisis pola komunikasi, dan menghasilkan laporan akhir.

---

#### Langkah 1: Akuisisi Data WhatsApp

| Langkah | Aktor | Aksi | Sistem | Output |
|---|---|---|---|---|
| 1.1 | Investigator | Hubungkan ponsel saklar ke laptop lewat USB | Backend menerima koneksi ADB | Device terdeteksi |
| 1.2 | Investigator | Jalankan WhatsApp extractor (CLI) | `extract-keys.py` → `decrypt-wa.py` → `merge_dbs_sqlite.py` | `msgstore.db` terdekripsi dan digabung |
| 1.3 | System | WhatsApp data otomatis diunggah ke sistem | Celery worker memproses file WhatsApp | Data tersimpan di tabel `whatsapp_data` dan `whatsapp_messages` |
| 1.4 | Investigator | Verifikasi data WhatsApp sudah ter-extrak | Sistem menampilkan status ekstraksi | Status: "Data terintegrasi — 342 percakapan, 15,892 pesan" |

**Komponen terlibat:** d.5.1 (WhatsApp Data Acquisition), `extractors/whatsapp_extractor/`

---

#### Langkah 2: Registrasi Kasus dan Evidence

| Langkah | Aktor | Aksi | Sistem | Output |
|---|---|---|---|---|
| 2.1 | Investigator | Klik "Daftar Kasus Baru" | Form registrasi kasus terbuka (d.6.1) | Form kosong |
| 2.2 | Investigator | Isi: judul, deskripsi, prioritas (High), unit penanggung jawab | Sistem validasi RBAC diri sendiri | Kasus dibuat dengan ID |
| 2.3 | Investigator | Klik "Registrasi Barang Bukti" | Form registrasi barang bukti terbuka (d.7.2) | Form kosong |
| 2.4 | Investigator | Scan barcode IMEI ponsel, foto, koordinat lokasi perolehan | Sistem menghitung SHA-256 dan menyimpan metadata | Barang bukti terdaftar dengan hash SHA-256 |
| 2.5 | System | Otomatis link WhatsApp data ke kasus | Foreign key `case_id` di `whatsapp_data` | WhatsApp data terhubung ke kasus |
| 2.6 | System | Generate audit log | `audit_logs` mencatat aksi registrasi | Log: "Case created", "Evidence registered" |

**Komponen terlibat:** d.6.1, d.7.1, d.7.2, d.7.5

---

#### Langkah 3: Analisis Komunikasi WhatsApp

| Langkah | Aktor | Aksi | Sistem | Output |
|---|---|---|---|---|
| 3.1 | Investigator | Pilih kasus → pilih "WhatsApp Intelligence" | Sistem menampilkan WhatsApp data terintegrasi | Daftar percakapan WhatsApp |
| 3.2 | Investigator | Klik "Communication Profile Analyzer" | Sistem menganalisis pola komunikasi | Ringkasan: kontak dominan, grup aktif, pola waktu |
| 3.3 | Investigator | Klik "AI Context Mapping" untuk kontak tertentu | ML worker menjalankan NLP/LLM pipeline | Topik, entitas, kata kunci — visualisasi hubungan |
| 3.4 | Investigator | Gunakan pencarian: keyword "transfer", tanggal 1-15 Agustus | Sistem filter dan index | Hasil pencarian 23 pesan relevan |

**Komponen terlibat:** d.5.2, d.5.3, d.5.4

---

#### Langkah 4: Analisis Bukti dan Chain of Custody

| Langlangkah | Aktor | Aksi | Sistem | Output |
|---|---|---|---|---|
| 4.1 | Investigator | Pilih "Evidence Management" | Sistem menampilkan daftar barang bukti untuk kasus | Ponsel saklar dengan status "Terdaftar" |
| 4.2 | Supervisor | Klik "Transfer Approval" | Sistem mengirim notifikasi ke penerima | Approval workflow dimulai |
| 4.3 | Supervisor | Konfirmasi penerimaan | Sistem mencatat serah terima di `custody_logs` | Status custody diperbarui, BAST dapat di-generate |
| 4.4 | Investigator | Generate BAST | Sistem membuat PDF laporan serah terima | BAST PDF siap di-download |
| 4.5 | System | Verifikasi integritas otomatis | SHA-256 hash dihitung ulang dan dibandingkan | Status integritas: "Verified" |

**Komponen terlibat:** d.7.3, d.7.4, d.7.5, d.7.7

---

#### Langkah 5: Analisis Strategis dan Intelligence

| Langkah | Aktor | Aksi | Sistem | Output |
|---|---|---|---|---|
| 5.1 | Investigator | Upload dokumen CSV hasil ekstraksi | Sistem kirim ke NER worker | Entitas terdeteksi: 15 nama, 8 lokasi, 3 tanggal |
| 5.2 | Investigator | Klik "Relationship Link Analysis" | Sistem build graph dari data WhatsApp + entitas NER | Visualisasi graf hubungan antar kontak dan entitas |
| 5.3 | Investigator | Upload file APK m suspect | Sistem kirim ke APK analysis worker | Manifest parsed, 12 izin terdeteksi, sertifikat diverifikasi |
| 5.4 | Investigator | Buka Advanced Analysis Dashboard | Sistem menampilkan metrik real-time | Metrics: 3 file diproses, 1 job berjalan, latency 120ms |

**Komponen terlibat:** d.8.1, d.8.2, d.8.3, d.8.4

---

#### Langkah 6: Pelaporan dan Penyelesaian Kasus

| Langkah | Aktor | Aksi | Sistem | Output |
|---|---|---|---|---|
| 6.1 | Investigator | Generate laporan kasus | Sistem menggabungkan: WhatsApp data, evidence log, NER results, graph analysis | PDF laporan kasus lengkap |
| 6.2 | Investigator | Update status kasus ke "Closed" | Sistem mencatat di `audit_logs` | Status kasus: "Closed" |
| 6.3 | Supervisor | Download semua laporan | Sistem export package | ZIP berisi: laporan kasus PDF, BAST PDF, evidence CSV, graph visualization |

**Komponen terlibat:** d.6.2, d.6.8, d.7.7

---

## 5. Skenario-Skenario Alternatif

### Skenario B: Mobile Deployment — Laboratorium Bergerak

Di skenario ini, seluruh komponen berjalan di dalam kendaraan operasional (mobile lab).

#### Aktor: Investigator (di dalam kendaraan)

| Tahap | Alur |
|---|---|
| **Setup** | Backend, Redis, PostgreSQL, dan Celery workers berjalan di dalam kendaraan (NAS 80TB, vehicle server) |
| **Akuisisi Offline** | WhatsApp extractor berjalan di laptop di dalam kendaraan — tidak perlu internet |
| **Sinkronisasi** | Ketika ada koneksi (satelit/seluler), data otomatis tersinkronisasi ke server pusat |
| **Analysis On-Field** | Semua modul (d.5–d.8) dapat diakses langsung dari laptop di dalam kendaraan |

#### Kebutuhan Khusus
- Internet satelit/seluler untuk sinkronisasi (d.3.6 Solution Pack)
- Portable power station untuk daya cadangan (d.3.1 Solution Pack)
- NAS 80TB untuk penyimpanan lokal (d.3.7 Solution Pack)

---

### Skenario C: Role-Based Access Control (RBAC) Demo

#### Aktor: Admin, Investigator, Viewer

| Aktivitas | Admin | Investigator | Viewer |
|---|---|---|---|
| Registrasi kasus | ✅ | ✅ | ❌ |
| Update status kasus | ✅ | ✅ | ❌ |
| Lihat semua kasus | ✅ | Kasus yang ditugaskan | Kasus yang diizinkan |
| Edit hak akses pengguna | ✅ | ❌ | ❌ |
| Daftar barang bukti | ✅ | ✅ | ❌ |
| Pindahkan barang bukti | ✅ | ✅ | ❌ |
| Generate laporan BAST | ✅ | ✅ | ❌ |
| Jalankan NER analysis | ✅ | ✅ | ❌ |
| Lihat dashboard analytics | ✅ | ✅ | ✅ (read-only) |
| Export laporan | ✅ | ✅ | ✅ (read-only) |
| System audit log | ✅ | ❌ | ❌ |

---

## 6. Data Flow Scenarios

### 6.1 WhatsApp Data Ingestion

```
[USB Device]
    │
    ▼
[WhatsApp Extractor CLI]
    │ (extract-keys.py → decrypt-wa.py → merge_dbs_sqlite.py)
    ▼
[msgstore.db decrypted]
    │
    ▼
[Upload ke API d.5.1]
    │ POST /api/v1/whatsapp/upload
    ▼
[WhatsApp Ingestion Worker (Celery)]
    │ - Parse SQLite tables
    - Validasi data
    - Ekstrak contacts, messages, media references
    ▼
[Database Storage]
    │ - whatsapp_data table
    - whatsapp_messages table
    - evidence table (jika ada file media)
    ▼
[Indexing Worker]
    │ - Full-text index untuk pencarian (d.5.4)
    - Communication profile pre-compute (d.5.2)
    ▼
[Cache Layer (Redis)]
    │ - Cache search results
    - Cache profile summaries
    ▼
[Ready for Analysis]
    │ - Available untuk d.5.2, d.5.3, d.5.4
    - Available untuk d.8.1 NER (jika CSV/PDF)
```

### 6.2 Evidence Chain of Custody

```
[Evidence Received at Scene]
    │ - Device with IMEI, serial number
    - GPS coordinates
    - Photo of device
    ▼
[Evidence Registration (d.7.2)]
    │ - Metadata recorded
    - SHA-256 hash calculated
    ▼
[Central Repository (d.7.1)]
    │ - Stored in evidence table
    - Indexed by case, category, location
    ▼
[Custody Log Entry (d.7.3)]
    │ - Initial custody entry
    - Holder: Evidence Custodian
    ▼
[Transfer Request (d.7.4)]
    │ - Approval workflow
    - Two-party confirmation (sender + receiver)
    ▼
[Transfer Approved]
    │ - New custody log entry
    - SHA-256 re-verification
    - BAST update
    ▼
[Evidence Archived]
    │ - Can generate Custody Report (d.7.7)
    - Geospatial tracking (d.7.8)
```

### 6.3 Strategic Intelligence Pipeline

```
[Akuisisi Data Mentah]
    │ - WhatsApp messages (d.5)
    - Document files (CSV, PDF)
    - APK files
    ▼
[Document Upload (d.8.1)]
    │ POST /api/v1/intelligence/ner
    ▼
[NER Worker (Celery)]
    │ - Extract text (pdfplumber, pandas)
    - Run NER model (spaCy/transformers)
    - Extract entities: person, location, org, date
    - Return structured entities
    ▼
[Graph Construction (d.8.2)]
    │ - Build relationships from entities
    - Calculate edge weights (frequency of interaction)
    - Generate graph data
    ▼
[APK Analysis (d.8.3)]
    │ POST /api/v1/intelligence/apk-analysis
    ▼
[APK Worker (Celery)]
    │ - Parse AndroidManifest.xml
    - Extract permissions
    - Analyze DEX bytecode for threats
    - Extract certificate info
    ▼
[Dashboard Aggregation (d.8.4)]
    │ - Collect metrics from all workers
    - Update dashboard cache (Redis)
    - Serve real-time metrics
    ▼
[Visualization]
    │ - Web dashboard
    - Graph visualization (React Flow)
    - Geospatial map (Leaflet)
```

---

## 7. Error Handling Scenarios

### 7.1 WhatsApp Extraction Failure

| Error | Trigger | Response |
|---|---|---|
| `WA-001` | WhatsApp backup tidak dapat diekstrak | Sistem memberi notifikasi, error log, dan retry mechanism |
| `WA-002` | Database WhatsApp corrupt | Sistem memberi opsi restore dari backup, atau skip file |
| `WA-003` | Encryption key tidak ditemukan | Sistem error dengan pesan "Key extraction failed — device tidak terhubung dengan benar" |

### 7.2 Case Management Errors

| Error | Trigger | Response |
|---|---|---|
| `CASE-001` | Kasus sudah ada | Error 409 Conflict dengan pesan |
| `CASE-002` | User tidak memiliki akses | Error 403 Forbidden |
| `CASE-003` | Delete kasus aktif | Error 400 — harus close kasus dulu |

### 7.3 Evidence Integrity Errors

| Error | Trigger | Response |
|---|---|---|
| `EVID-001` | SHA-256 mismatch | Sistem beri notifikasi "Integrity compromised", flag evidence sebagai suspicious |
| `EVID-002` | Transfer approval ditolak | Status transfer kembali ke holder semula, audit log dicatat |

### 7.4 Intelligence Errors

| Error | Trigger | Response |
|---|---|---|
| `NER-001` | Dokumen tidak dapat diproses | Error 400 — format tidak didukung |
| `APK-001` | APK rusak/corrupt | Error 422 — "APK file invalid" |
| `GRAPH-001` | Graph terlalu besar | Error 413 — "Dataset too large, please filter" |

---

## 8. Performance Scenarios

### 8.1 Concurrent User Scenarios

| Scenario | Users | Expected Response | Notes |
|---|---|---|---|
| Investigation Dashboard refresh | 10 users | < 2s | Cached metrics |
| WhatsApp search (keyword) | 5 users | < 1s | Full-text index |
| Case creation | 3 users | < 500ms | Straightforward INSERT |
| NER inference (batch 10 docs) | 2 users | < 30s | Async via Celery |
| Evidence SHA-256 verification | 1 user | < 10s | Depends on file size |
| APK static analysis | 1 user | < 1s | Fast parsing |
| Graph analysis (1000 nodes) | 1 user | < 5s | Cached result |

### 8.2 Offline Mode (Mobile Lab)

| Komponen | Offline Capable | Notes |
|---|---|---|
| d.5 WhatsApp Extractor | ✅ | CLI-based, tidak perlu server |
| d.6 Case Management | ✅ | SQLite database lokal |
| d.7 Evidence Management | ✅ | Data tersimpan lokal |
| d.8 Intelligence | ⚠️ Limited | NER/APK analysis butuh model (bisa di-bundle) |
| Dashboard | ✅ | Data dari local database |
| Reporting | ✅ | PDF generation lokal |

---

## 9. Business Rules

### 9.1 Case Lifecycle

```
OPEN → IN_PROGRESS → ON_HOLD → RESOLVED → CLOSED
```

| Status | Transisi yang Diizinkan | Syarat |
|---|---|---|
| Open | → In Progress | Investigator assigned |
| In Progress | → On Hold | User manually set |
| In Progress | → Resolved | Semua task selesai |
| On Hold | → In Progress | Resume button |
| Resolved | → Closed | Supervisor approve |
| Closed | (none) | Final state, read-only |

### 9.2 Evidence State Machine

```
RECEIVED → IN_CUSTODY → TRANSFERRED → IN_CUSTODY → ... → ARCHIVED
```

| Status | Syarat Transisi |
|---|---|
| Received | Evidence baru terdaftar |
| In Custody | Ada custody log entry |
| Transferred | Transfer approval approved |
| Archived | Case closed, evidence tidak lagi diperlukan |

### 9.3 SHA-256 Integrity Rules

| Aturan | Keterangan |
|---|---|
| Auto-hash at registration | SHA-256 dihitung otomatis saat evidence didaftarkan (d.7.2) |
| Integrity check on transfer | SHA-256 diverifikasi sebelum setiap transfer (d.7.4) |
| Periodic re-verification | Hash dicek kembali setiap 30 hari |
| Hash mismatch | Evidence di-flag "compromised", semua aksi diblokir |

---

## 10. Scenario Summary

| No | Skenario | Aktor | Komponen Terlibat | Priority |
|---|---|---|---|---|
| 1 | Investigator menyelidiki kasus WhatsApp | Investigator | d.5, d.6, d.7, d.8 | High |
| 2 | Mobile deployment di kendaraan operasional | Investigator | Semua modul (offline mode) | Medium |
| 3 | Role-based access control demo | Admin, Investigator, Viewer | d.6.6 (RBAC) | High |
| 4 | Akuisisi data WhatsApp via USB | Investigator | d.5.1, WhatsApp Extractor CLI | High |
| 5 | Chain of custody lengkap | Investigator, Supervisor | d.7.3, d.7.4, d.7.7 | Critical |
| 6 | Analisis intelligence (NER + Graph + APK) | Investigator | d.8.1, d.8.2, d.8.3 | Medium |
| 7 | Generate laporan akhir kasus | Investigator | d.6.8, d.7.7 | High |

---

## 11. Key Design Decisions

1. **Monolith modular dengan Celery workers** — Semua modul (d.5–d.8) berjalan sebagai service terpisah di dalam satu aplikasi backend, dengan Celery workers untuk tugas berat. Ini memudahkan deployment mobile (single server) dan development.

2. **SQLite sebagai bridge WhatsApp data** — WhatsApp databases (`msgstore.db`) yang diekstrak menggunakan SQLite parser, lalu data dimigrasikan ke PostgreSQL untuk konsistensi.

3. **JWT + RBAC untuk authentication** — Semua endpoint dilindungi oleh JWT token dan RBAC middleware, memastikan data sensitif hanya bisa diakses oleh role yang berwenang.

4. **SHA-256 mandatory untuk evidence** — Setiap barang bukti digital harus melewati hashing SHA-256 saat didaftarkan dan diverifikasi saat setiap perpindahan.

5. **Offline-first untuk mobile deployment** — Dikarenakan laboratorium bergerak mungkin tidak selalu memiliki koneksi internet, semua komponen dirancang untuk berfungsi offline dengan sync ke pusat ketika koneksi tersedia.

6. **Async task processing** — Tugas berat (NER, APK analysis, SHA-256 hashing, PDF generation) diproses secara asynchronous via Celery untuk menjaga API tetap responsif.

7. **PostgreSQL untuk produksi, SQLite untuk dev** — SQLite digunakan untuk development dan testing cepat, PostgreSQL untuk produksi dengan fitur ACID dan connection pooling.

8. **Full-text search untuk WhatsApp data** — Menggunakan PostgreSQL full-text search atau Redis search untuk pencarian cepat data WhatsApp (d.5.4).

9. **Graph data stored as JSONB** — Graph nodes dan edges disimpan dalam format JSON di PostgreSQL untuk fleksibilitas dan kemudahan serialisasi ke frontend.

10. **PDF generation via WeasyPrint** — Pemilihan WeasyPrint untuk laporan PDF karena kualitas tinggi, dukungan CSS, dan integrasi dengan Python yang baik.
