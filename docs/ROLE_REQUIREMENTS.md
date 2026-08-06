# Kebutuhan Peran Tim Proyek Evidentra

## Dokumen Kebutuhan Peran untuk Tim Cyber

| Properti | Nilai |
|---|---|
| **Nama Proyek** | Evidentra Digital Forensics & Intelligence Platform |
| **Dokumen Sumber** | `Spectek_Digital_Forensics_Intelligence_Module.pdf`, `Solution_Pack_Digifor_Brimob.pdf` |
| **Versi** | 1.0 |
| **Tanggal** | 2026-08-05 |

---

## 1. Tech Stack yang Sudah Ada di Proyek

Sebelum mendefinisikan kebutuhan peran, berikut teknologi yang sudah digunakan di proyek ini:

| Teknologi | Versi/Penggunaan | Keterangan |
|---|---|---|
| Python | 3.x (sistem: 3.14.6, venv: 3.11) | Bahasa utama seluruh proyek |
| SQLite | Bawaan Python (`sqlite3`) | Penyimpanan data WhatsApp (`msgstore.db`) |
| Protocol Buffers | `protobuf==7.35.1` | Serialisasi data WhatsApp crypto (`C14_cipher`, `C15_IV`, `key_type`, dll.) |
| PyCryptodome | `pycryptodomex==3.23.0` | Enkripsi/dekripsi AES untuk WhatsApp backup |
| javaobj-py3 | `javaobj-py3==0.5.0` | Deserialisasi objek Java (WhatsApp key format) |
| uiautomator2 | `uiautomator2==3.7.0` | Otomasi UI Android untuk akuisisi data |
| adbutils | `adbutils==2.12.0` | Komunikasi ADB dengan perangkat Android |
| Pillow | `pillow==12.3.0` | Pemrosesan gambar (metadata foto/video) |
| lxml | `lxml==6.1.1` | Parsing XML |
| requests | `requests==2.34.2` | HTTP client |
| pyright | Config di `pyrightconfig.json` | Type checking |

### Struktur Direktori yang Sudah Direncanakan (dari `pyrightconfig.json`)

```
brimob_forensiq/
├── backend/          ← sudah direncanakan
├── worker/           ← sudah direncanakan
├── extractors/
│   └── whatsapp_extractor/
│       └── backup/
```

---

## 2. Kebutuhan Backend Engineer

### 2.1 Bahasa dan Framework Utama

| Kategori | Teknologi | Alasan |
|---|---|---|
| **Bahasa** | Python 3.11+ | Sudah menjadi bahasa utama proyek, seluruh kode existing menggunakan Python |
| **Web Framework** | FastAPI | Async support, otomatis generate OpenAPI/Swagger docs, ringan, performa tinggi untuk API REST |
| **Alternatif Framework** | Flask | Jika tim lebih familiar; FastAPI lebih disarankan untuk fitur real-time dashboard |
| **ORM** | SQLAlchemy 2.0 | Abstraksi database, mendukung SQLite (dev) dan PostgreSQL (prod), migrasi schema via Alembic |
| **Database** | PostgreSQL (produksi), SQLite (dev/testing) | PostgreSQL untuk multi-user, ACID compliance, dan performa query kompleks (d.7 evidence queries) |
| **Authentication** | FastAPI Users / Authlib + JWT | Implementasi RBAC (d.6.6), verifikasi registrasi pengguna, pengaturan hak akses per level |
| **Password Hashing** | bcrypt / argon2-cffi | Penyimpanan password yang aman untuk IAM |
| **PDF Generation** | WeasyPrint atau ReportLab | d.6.8 (Report Generation Engine), d.7.7 (Custody Report / BAST) |
| **Background Task** | Celery + Redis atau asyncio | Untuk tugas berat: hashing SHA-256 (d.7.5), NER processing (d.8.1), APK analysis (d.8.3) |
| **Caching** | Redis | Dashboard real-time (d.6.2, d.8.4), caching hasil NER dan graph analytics |
| **API Validation** | Pydantic v2 | Validasi request/response, sudah terintegrasi dengan FastAPI |
| **Logging** | Python `logging` (standar) | Sudah digunakan di kode WhatsApp extractor; diperluas untuk audit log (d.6.7) |
| **Testing** | pytest + pytest-asyncio | Unit test dan integration test untuk semua modul |
| **Container** | Docker + Docker Compose | Deployment konsisten, isolasi environment untuk backend, worker, dan database |

### 2.2 Tanggung Jawab Per Sprint

#### Sprint 1 — Foundation

| Tugas | Detail |
|---|---|
| Setup project scaffold | Buat struktur `backend/`, `worker/`, `modules/d5_whatsapp/`, `modules/d6_operations/`, `modules/d7_evidence/`, `modules/d8_intelligence/` |
| Database schema design | Rancang schema PostgreSQL: tabel untuk kasus, tugas, bukti, pengguna, audit log, WhatsApp data |
| SQLAlchemy models | Implementasi ORM models untuk semua entitas |
| Alembic migrations | Setup migration pipeline |
| FastAPI app scaffold | Buat aplikasi FastAPI utama dengan routing structure |
| Pydantic schemas | Buat request/response schemas untuk semua endpoint |
| WhatsApp extractor integration | Integrasikan kode WhatsApp extractor ke `modules/d5_whatsapp/` + endpoint `POST /api/v1/whatsapp/import` |
| Redis setup | Setup Redis untuk caching dan Celery broker |

#### Sprint 2 — Case Platform API

| Tugas | Detail |
|---|---|
| Case CRUD API | Endpoint untuk d.6.1 (Case Registration) |
| Task CRUD API | Endpoint untuk d.6.3 (Task Assignment) |
| Dashboard data API | Endpoint `GET /api/v1/dashboard` untuk d.6.2 (Investigation Dashboard) — agregasi global kasus, prioritas, progres |
| Kanban API | Endpoint untuk d.6.4 (Kanban Workflow Tracking) — update status tugas |
| Auth scaffold | Implementasi JWT auth, endpoint login/register, middleware |
| RBAC middleware | Struktur dasar RBAC untuk kontrol akses endpoint |

#### Sprint 3 — Case Platform + Evidence API Part 1

| Tugas | Detail |
|---|---|
| Org Hierarchy API | Endpoint untuk d.6.5 (Organizational Hierarchy Portal) |
| RBAC lengkap | Implementasi penuh RBAC (d.6.6): role-based endpoint protection, user registration, role management |
| Audit Log API | Endpoint untuk d.6.7 (System Audit & Logging) — read-only log, middleware untuk pencatatan |
| PDF Report API | Endpoint untuk d.6.8 (Report Generation Engine) — generate PDF dari data kasus |
| Evidence Repository API | Endpoint untuk d.7.1 (Central Evidence Repository) — CRUD barang bukti |
| Evidence Registration API | Endpoint untuk d.7.2 (Evidence Registration Module) — metadata barang bukti |

#### Sprint 4 — Evidence API Part 2

| Tugas | Detail |
|---|---|
| Custody Tracking API | Endpoint untuk d.7.3 (Evidence Custody & Transfer Tracking) |
| Transfer Approval API | Endpoint untuk d.7.4 (Evidence Transfer Approval) — workflow persetujuan |
| SHA-256 Integrity API | Endpoint dan service untuk d.7.5 (Evidence Integrity Verification) — hashing otomatis |
| Asset Vault API | Endpoint untuk d.7.6 (Asset Vault Registry) — pengelompokan berdasarkan lokasi dan kategori |
| BAST Report API | Endpoint untuk d.7.7 (Custody Report Generator) — generate BAST PDF |
| Geospatial API | Endpoint untuk d.7.8 (Geospatial Evidence Tracking) — CRUD koordinat GPS/GIS |

#### Sprint 5 — Intelligence API Part 1

| Tugas | Detail |
|---|---|
| NER API | Endpoint untuk d.8.1 (Neural Document Correlation) — terima CSV/PDF, return extracted entities |
| Graph Analysis API | Endpoint untuk d.8.2 (Relationship Link Analysis) — terima data komunikasi, return graph data |
| APK Analysis API | Endpoint untuk d.8.3 (APK Static Analysis Inspector) — terima APK, return analysis results |
| ML Pipeline Service | Buat service layer untuk inference NER, graph analytics, APK parsing — integrasi dengan Celery worker |

#### Sprint 6 — Integration + Dashboard API

| Tugas | Detail |
|---|---|
| Advanced Dashboard API | Endpoint untuk d.8.4 (Advanced Analysis Dashboard) — metrik pemrosesan, status pekerjaan, hasil korelasi, latensi |
| Cross-module integration | Pastikan data mengalir antar modul: WhatsApp → Case → Evidence → Intelligence |
| Performance optimization | Optimasi query database, tambah indeks, implementasi caching untuk dashboard |
| API documentation | Finalisasi Swagger/OpenAPI docs untuk semua endpoint |
| Integration tests | Tulis dan jalankan integration tests untuk semua endpoint |

### 2.3 Dependencies

Semua dependensi Python dikelola dalam satu file `requirements.txt` (extractor, backend, ML, dev/testing).

### 2.4 File Requirements Proyek

| File | Isi |
|---|---|
| `requirements.txt` | Semua dependensi Python proyek |
| `frontend/package.json` | Dependensi frontend |

---

## 3. Kebutuhan ML/AI Specialist

### 3.1 Bahasa dan Framework Utama

| Kategori | Teknologi | Alasan |
|---|---|---|
| **Bahasa** | Python 3.11+ | Sudah menjadi bahasa utama proyek |
| **NLP/LLM Framework** | Hugging Face Transformers atau spaCy | d.5.3 (AI Context Mapping), d.8.1 (NER) — perlu model untuk Bahasa Indonesia |
| **NER Model** | spaCy (id pipeline) atau model Hugging Face (bert-base-indonesian) | Named Entity Recognition untuk identifikasi nama, objek, lokasi, tanggal |
| **Graph Analytics** | NetworkX atau igraph | d.8.2 (Relationship Link Analysis) — analisis dan visualisasi graf hubungan antar entitas |
| **Graph Visualization** | PyVis atau Graphviz | Visualisasi jaringan hubungan untuk dashboard |
| **APK Static Analysis** | androguard, apktool, jadx | d.8.3 (APK Static Analysis Inspector) — parsing Android Manifest, DEX, sertifikat |
| **Machine Learning** | scikit-learn | Klasifikasi, clustering (opsional untuk fitur lanjutan) |
| **Data Processing** | pandas, numpy | Pemrosesan data CSV/PDF untuk NER dan analisis |
| **PDF Parsing** | PyPDF2 atau pdfplumber | d.8.1 — ekstrak teks dari PDF untuk NER processing |
| **CSV Processing** | pandas | d.8.1 — baca dan proses data CSV hasil akuisisi |
| **Model Serving** | FastAPI + Celery | Inference model via API endpoint, diproses asinkron oleh worker |
| **Model Storage** | Local filesystem atau MinIO | Menyimpan model NER, graph models, dan APK analysis rules |
| **Async Tasks** | Celery + Redis | Menjalankan inference NER, graph analysis, APK parsing sebagai background task |
| **Testing** | pytest + pytest-asyncio | Unit test untuk pipeline ML dan model inference |

### 3.2 Tanggung Jawab Per Sprint

#### Sprint 1 — Foundation

| Tugas | Detail |
|---|---|
| NLP/LLM pipeline setup | Siapkan pipeline untuk AI Context Mapping (d.5.3) — pilih model, setup preprocessing |
| Model selection for NER | Evaluasi model NER Bahasa Indonesia: spaCy id, bert-base-indonesian, atau custom model |
| PDF/CSV parsing utilities | Buat utility untuk ekstrak teks dari PDF dan CSV yang akan diproses oleh NER |
| ML environment setup | Pastikan environment ML (GPU/CPU) tersedia, install dependencies |

#### Sprint 3 — ML Pipeline Foundation

| Tugas | Detail |
|---|---|
| NER model training/fine-tuning | Latih atau fine-tune model NER untuk konteks forensik digital (nama, objek, lokasi, tanggal) |
| NER inference service | Buat service untuk inference NER — terima dokumen CSV/PDF, return extracted entities |
| Graph analytics setup | Setup NetworkX/igraph untuk analisis hubungan antar entitas |
| APK analysis rules | Buat aturan parsing untuk Android Manifest, izin aplikasi, komponen, sertifikat |

#### Sprint 5 — Intelligence Features

| Tugas | Detail |
|---|---|
| d.8.1 Neural Document Correlation | Implementasi NER pipeline lengkap: terima CSV/PDF, ekstrak teks, running NER, return entities terstruktur |
| d.8.2 Relationship Link Analysis | Implementasi graph analytics: analisis frekuensi interaksi, build graph network, return visualization data |
| d.8.3 APK Static Analysis Inspector | Implementasi parser APK statis: extract Android Manifest, izin, komponen, sertifikat, analisis indikator ancaman pada DEX |
| ML Pipeline Service | Integrasikan semua model ke dalam Celery worker — NER inference, graph analysis, APK parsing |

#### Sprint 6 — Integration + Optimization

| Tugas | Detail |
|---|---|
| Model performance tuning | Optimasi latency inference NER dan graph analytics |
| Dashboard data integration | Pastikan hasil NER, graph analysis, dan APK analysis tersedia untuk d.8.4 Advanced Analysis Dashboard |
| Model documentation | Dokumentasi model, accuracy metrics, dan cara penggunaan |

### 3.3 Dependencies yang Perlu Diinstall

```
spacy>=3.7.0
spacy-lookups-data>=1.0.5
# Model ID: python -m spacy download id_core_news_sm
transformers>=4.35.0
torch>=2.0.0
networkx>=3.0
matplotlib>=3.7.0
pyvis>=0.3.0
graphviz>=0.20.0
androguard>=3.4.0
pdfplumber>=0.10.0
pandas>=2.0.0
numpy>=1.24.0
scikit-learn>=1.3.0
celery>=5.3.0
redis>=5.0.0
```

---

## 4. Kebutuhan Frontend Engineer

### 4.1 Bahasa dan Framework Utama

| Kategori | Teknologi | Alasan |
|---|---|---|
| **Bahasa** | TypeScript (JavaScript dengan typing) | Type safety untuk aplikasi skala menengah, lebih mudah di-maintain |
| **Framework** | React 18+ atau Vue 3 | Component-based UI, ecosystem yang luas, cocok untuk dashboard dan SPA |
| **Alternatif Framework** | Vue 3 + Vite | Lebih ringan dan faster development jika tim lebih familiar |
| **State Management** | Zustand (React) atau Pinia (Vue) | Simple state management untuk dashboard dan form-heavy app |
| **HTTP Client** | Axios atau fetch API | Komunikasi dengan backend FastAPI REST API |
| **UI Component Library** | Tailwind CSS + shadcn/ui atau Ant Design | Styling cepat, component library yang lengkap (table, form, modal, dashboard) |
| **Charting** | Chart.js atau Recharts | d.6.2 (Investigation Dashboard), d.8.4 (Advanced Analysis Dashboard) — visualisasi data |
| **Graph Visualization** | React Flow atau Cytoscape.js | d.8.2 (Relationship Link Analysis) — visualisasi graf hubungan antar entitas |
| **Map Visualization** | Leaflet.js atau Mapbox GL JS | d.7.8 (Geospatial Evidence Tracking) — peta koordinat lokasi perolehan bukti |
| **Kanban Board** | Custom component atau @hello-pangea/dnd | d.6.4 (Kanban Workflow Tracking) — drag-and-drop Kanban board |
| **Form Handling** | React Hook Form atau VueUse Form | Form untuk case registration, evidence registration, task assignment |
| **PDF Preview** | react-pdf atau pdf.js | Preview laporan PDF (d.6.8, d.7.7) di browser |
| **Build Tool** | Vite | Fast build dan HMR (Hot Module Replacement) |
| **Testing** | Vitest + React Testing Library | Unit test dan component test |
| **E2E Testing** | Playwright | End-to-end testing untuk alur kerja utama |
| **Type Checking** | TypeScript compiler (tsc) | Type safety, sudah ada `pyrightconfig.json` untuk backend — konsistensi di frontend |

### 4.2 Tanggung Jawab Per Sprint

#### Sprint 1 — Foundation

| Tugas | Detail |
|---|---|
| Project scaffold | Buat proyek React/Vue dengan Vite, TypeScript, Tailwind CSS |
| Layout dan routing | Setup layout utama (sidebar, header, content area) dan routing (React Router / Vue Router) |
| API client setup | Buat API client module untuk komunikasi dengan backend FastAPI |
| Auth UI components | Buat komponen login dan register |
| WhatsApp data viewer | Buat komponen untuk menampilkan data WhatsApp yang sudah diekstrak (list chat, kontak, pesan) |
| Search and filter UI | Buat komponen search/filter untuk d.5.4 |

#### Sprint 2 — Case Platform UI

| Tugas | Detail |
|---|---|
| Case Registration form | Form untuk d.6.1 — pendaftaran kasus baru dengan metadata lengkap |
| Investigation Dashboard | Dashboard visual untuk d.6.2 — ringkasan kasus, prioritas, beban tugas, progres (Chart.js/Recharts) |
| Task Assignment form | Form untuk d.6.3 — penugasan tugas dengan checklist, tenggat waktu, urgensi |
| Kanban Board | Implementasi d.6.4 — papan kerja Kanban dengan drag-and-drop (TODO → IN_PROGRESS → DONE) |

#### Sprint 3 — Case Platform UI Part 2 + Evidence UI Part 1

| Tugas | Detail |
|---|---|
| Org Hierarchy Viewer | Visualisasi struktur organisasi untuk d.6.5 (bisa pakai Tree component atau D3.js) |
| RBAC UI | Panel manajemen pengguna dan role untuk d.6.6 |
| Audit Log Viewer | Tabel read-only untuk d.6.7 — menampilkan log aktivitas pengguna |
| Report Preview | Komponen untuk preview dan download laporan PDF (d.6.8) |
| Evidence Repository UI | Tabel dan filter untuk d.7.1 — daftar barang bukti berdasarkan kasus dan kategori |
| Evidence Registration Form | Form untuk d.7.2 — input metadata barang bukti (jenis, merek, IMEI, nomor seri, kapasitas, foto, koordinat) |

#### Sprint 4 — Evidence UI Part 2

| Tugas | Detail |
|---|---|
| Custody Timeline | Visualisasi riwayat penguasaan barang bukti untuk d.7.3 |
| Transfer Approval UI | UI untuk d.7.4 — tampilkan permintaan serah terima, tombol konfirmasi kirim/penerima |
| Integrity Verification status | Tampilkan status hash SHA-256 dan hasil verifikasi untuk d.7.5 |
| Asset Vault UI | Tampilan pengelompokan barang bukti berdasarkan lokasi dan kategori untuk d.7.6 |
| BAST Report Preview | Preview dan download BAST PDF untuk d.7.7 |
| Geospatial Map | Peta interaktif (Leaflet/Mapbox) untuk d.7.8 — tampilkan koordinat lokasi perolehan bukti |

#### Sprint 5 — Intelligence UI Part 1

| Tugas | Detail |
|---|---|
| NER Document Viewer | Upload CSV/PDF dan tampilkan hasil NER (d.8.1) — entitas yang teridentifikasi dengan highlight |
| Relationship Graph | Visualisasi graf hubungan antar entitas untuk d.8.2 (React Flow atau Cytoscape.js) |
| APK Analysis Viewer | Tampilkan hasil analisis APK statis untuk d.8.3 — Android Manifest, izin, komponen, sertifikat |

#### Sprint 6 — Dashboard + Integration

| Tugas | Detail |
|---|---|
| Advanced Analysis Dashboard | Dashboard analitik lengkap untuk d.8.4 — metrik pemrosesan, jumlah berkas, status pekerjaan, hasil korelasi, latensi (Chart.js) |
| Cross-module navigation | Pastikan navigasi antar modul (WhatsApp → Cases → Evidence → Intelligence) mulus |
| End-to-end testing | Tulis Playwright E2E tests untuk alur kerja utama |
| Performance optimization | Optimasi rendering untuk dashboard dan graf yang besar |
| UI documentation | Dokumentasi komponen dan panduan penggunaan UI |

### 4.3 Dependencies yang Perlu Diinstall

```
react>=18.2.0   # atau vue@3
typescript>=5.0.0
vite>=5.0.0
tailwindcss>=3.4.0
@tanstack/react-query>=5.0.0   # atau vue-query
axios>=1.6.0
recharts>=2.0.0
reactflow>=11.0.0   # atau cytoscape.js
leaflet>=1.9.0
@hello-pangea/dnd>=16.0.0
react-hook-form>=7.0.0
vitest>=1.0.0
@testing-library/react>=14.0.0
playwright>=1.40.0
```

---

## 5. Kebutuhan QA Engineer

### 5.1 Bahasa dan Framework Utama

| Kategori | Teknologi | Alasan |
|---|---|---|
| **Bahasa** | Python 3.11+ | Sudah menjadi bahasa utama proyek, konsisten dengan stack backend |
| **Testing Framework** | pytest + pytest-asyncio | Sudah digunakan oleh Backend Engineer; QA Engineer memperluas coverage |
| **API Testing** | httpx + pytest-httpx | Testing endpoint REST API FastAPI secara langsung |
| **E2E Testing** | Playwright | Testing alur kerja end-to-end dari perspektif pengguna (browser) |
| **Performance Testing** | Locust atau k6 | Testing performa API saat beban tinggi (dashboard real-time, NER inference) |
| **Security Testing** | OWASP ZAP + bandit | Scanning kerentanan keamanan pada API dan kode Python |
| **Database Testing** | pytest + SQLAlchemy test fixtures | Testing migrasi database, integrity constraints, dan query correctness |
| **Test Reporting** | pytest-html atau Allure | Laporan hasil testing yang terstruktur dan mudah dibaca |
| **CI/CD Integration** | GitHub Actions atau Makefile | Menjalankan test suite secara otomatis pada setiap commit/pull request |
| **Test Data Management** | Faker + factory_boy | Membuat test data sintetis untuk kasus, bukti, pengguna, dan WhatsApp data |
| **API Contract Testing** | pytest + schemas | Validasi bahwa response API sesuai dengan Pydantic schemas |
| **Manual Testing** | TestRail atau spreadsheet | Dokumentasi manual test cases dan defect tracking |

### 5.2 Tanggung Jawab Per Sprint

#### Sprint 1 — Foundation

| Tugas | Detail |
|---|---|
| Test strategy & planning | Buat rencana testing keseluruhan: unit test, integration test, E2E test, performance test |
| Test environment setup | Siapkan environment testing terisolasi (Docker Compose) |
| Test scaffolding | Buat conftest.py, fixtures, dan base test classes untuk pytest |
| Unit test templates | Buat template unit test untuk model, service, dan API layer |
| Test data factories | Setup factory_boy factories untuk semua entitas database |
| Backend unit tests | Tulis unit tests untuk semua endpoint yang diimplementasi di Sprint 1 |
| API contract validation | Validasi bahwa response API sesuai Pydantic schemas |

#### Sprint 2 — Case Platform Testing

| Tugas | Detail |
|---|---|
| Case API tests | Tulis unit dan integration tests untuk d.6.1 Case Registration API |
| Task API tests | Tulis unit dan integration tests untuk d.6.3 Task Assignment API |
| Dashboard API tests | Tulis integration tests untuk d.6.2 Investigation Dashboard API |
| Kanban API tests | Tulis integration tests untuk d.6.4 Kanban Workflow Tracking API |
| Auth API tests | Tulis unit tests untuk endpoint login, register, dan RBAC middleware |
| RBAC test matrix | Buat matrix test untuk setiap role (admin, investigator, viewer) dan akses endpoint |
| E2E test cases | Tulis Playwright E2E tests untuk alur kerja case registration dan task assignment |
| Performance baseline | Jalankan load test pada API endpoint untuk establish baseline |

#### Sprint 3 — Case Platform + Evidence Testing

| Tugas | Detail |
|---|---|
| Org Hierarchy API tests | Integration tests untuk d.6.5 |
| RBAC full tests | Tulis comprehensive tests untuk semua role dan permission combinations |
| Audit Log API tests | Integration tests untuk d.6.7 — pastikan log tercatat dengan benar |
| PDF Report API tests | Integration tests untuk d.6.8 — validasi PDF dihasilkan dan berisi data yang benar |
| Evidence Repository API tests | Integration tests untuk d.7.1 |
| Evidence Registration API tests | Integration tests untuk d.7.2 — validasi metadata lengkap |
| Chain of Custody E2E | E2E test untuk alur custody: registrasi → serah terima → verifikasi |
| Security scanning | Jalankan OWASP ZAP dan bandit pada endpoint baru |

#### Sprint 4 — Evidence Management Testing

| Tugas | Detail |
|---|---|
| Custody Tracking API tests | Integration tests untuk d.7.3 — validasi riwayat penguasaan |
| Transfer Approval API tests | Integration tests untuk d.7.4 — validasi workflow persetujuan |
| SHA-256 Integrity API tests | Integration tests untuk d.7.5 — validasi hashing dan deteksi perubahan |
| Asset Vault API tests | Integration tests untuk d.7.6 |
| BAST Report API tests | Integration tests untuk d.7.7 — validasi BAST PDF |
| Geospatial API tests | Integration tests untuk d.7.8 — validasi koordinat GPS/GIS |
| Evidence E2E workflow | E2E test lengkap: registrasi bukti → serah terima → BAST → verifikasi integritas |
| Performance testing | Load test SHA-256 hashing untuk dataset besar |

#### Sprint 5 — Intelligence Testing

| Tugas | Detail |
|---|---|
| NER API tests | Integration tests untuk d.8.1 — validasi NER extraction accuracy |
| Graph Analysis API tests | Integration tests untuk d.8.2 — validasi graph data structure |
| APK Analysis API tests | Integration tests untuk d.8.3 — validasi parsing APK dan hasil analysis |
| ML Pipeline tests | Unit tests untuk Celery worker — NER inference, graph analysis, APK parsing |
| NER accuracy testing | Evaluasi accuracy NER model pada dataset sample forensik |
| Graph visualization tests | Validasi bahwa graph data yang dikirim ke frontend valid dan renderable |
| APK analysis edge cases | Testing APK dengan edge cases: APK rusak, APK tanpa manifest, APK dengan izin mencurigakan |
| ML model regression tests | Pastikan model NER dan graph analytics tidak regression antar sprint |

#### Sprint 6 — Integration + Full Regression

| Tugas | Detail |
|---|---|
| Cross-module integration tests | Tulis integration tests untuk alur lintas modul: WhatsApp → Case → Evidence → Intelligence |
| Full regression suite | Jalankan seluruh test suite — pastikan tidak ada regression |
| End-to-end full workflow | E2E test dari akuisisi WhatsApp → pembuatan kasus → registrasi bukti → analisis intelligence → laporan PDF |
| Performance optimization testing | Validasi performa dashboard dan query kompleks |
| Security audit | Full security scan OWASP ZAP pada seluruh API |
| Test coverage report | Generate laporan coverage pytest — target minimal 80% |
| Test documentation | Dokumentasi semua test cases, cara menjalankan, dan interpretasi hasil |
| Bug triage | Triage semua defect yang ditemukan, prioritaskan fix untuk release |

### 5.3 Dependencies yang Perlu Diinstall

```
pytest>=7.0.0
pytest-asyncio>=0.23.0
pytest-httpx>=0.25.0
pytest-html>=3.2.0
httpx>=0.25.0
factory-boy>=3.3.0
faker>=22.0.0
playwright>=1.40.0
locust>=2.0.0
bandit>=1.7.0
pyyaml>=6.0.0
```

---

## 6. Ringkasan Peran dan Tanggung Jawab

| Peran | Bahasa/Framework | Fokus Utama | Sprint Aktif |
|---|---|---|---|
| **Backend Engineer** | Python, FastAPI, SQLAlchemy, PostgreSQL, Redis, Celery | API REST, database schema, auth/RBAC, PDF generation, background tasks, integrasi modul | Sprint 1–6 |
| **ML/AI Specialist** | Python, spaCy/Transformers, NetworkX, androguard, PyPDF2 | NER pipeline, graph analytics, APK static analysis, ML model serving, performance tuning | Sprint 1, 3–6 |
| **Frontend Engineer** | TypeScript, React/Vue, Tailwind CSS, Chart.js, Leaflet | Dashboard UI, Kanban board, form, map visualization, graph visualization, report preview | Sprint 1–6 |
| **QA Engineer** | Python, pytest, Playwright, Locust, OWASP ZAP | Test strategy, unit/integration/E2E testing, performance testing, security testing, test coverage | Sprint 1–6 |

---

## 7. Matriks Tanggung Jawab (RACI)

| Fitur | Backend | ML/AI | Frontend | QA |
|---|---|---|---|---|
| d.5.1 WhatsApp Data Acquisition | R | C | I | I |
| d.5.2 Communication Profile Analyzer | R | C | I | I |
| d.5.3 AI Context Mapping | C | R | I | I |
| d.5.4 Search, Filter & Insight Reporting | R | C | R | I |
| d.6.1 Case Registration | R | I | R | I |
| d.6.2 Investigation Dashboard | R | C | R | I |
| d.6.3 Task Assignment | R | I | R | I |
| d.6.4 Kanban Workflow Tracking | R | I | R | I |
| d.6.5 Organizational Hierarchy Portal | R | I | R | I |
| d.6.6 Identity & Access Management | R | I | R | I |
| d.6.7 System Audit & Logging | R | I | R | I |
| d.6.8 Report Generation Engine | R | I | R | I |
| d.7.1 Central Evidence Repository | R | I | R | I |
| d.7.2 Evidence Registration Module | R | I | R | I |
| d.7.3 Evidence Custody & Transfer Tracking | R | I | R | I |
| d.7.4 Evidence Transfer Approval | R | I | R | I |
| d.7.5 Evidence Integrity Verification | R | I | I | I |
| d.7.6 Asset Vault Registry | R | I | R | I |
| d.7.7 Custody Report Generator | R | I | R | I |
| d.7.8 Geospatial Evidence Tracking | R | I | R | I |
| d.8.1 Neural Document Correlation | C | R | R | I |
| d.8.2 Relationship Link Analysis | C | R | R | I |
| d.8.3 APK Static Analysis Inspector | C | R | R | I |
| d.8.4 Advanced Analysis Dashboard | R | C | R | I |

Keterangan: **R** = Responsible, **C** = Consulted, **I** = Informed

---

## 8. Catatan Penting

1. **Backend Engineer** adalah peran paling sentral — semua fitur bergantung pada API yang disediakan.
2. **ML/AI Specialist** mulai aktif di Sprint 1 (setup) dan Sprint 3 (pipeline), dengan implementasi fitur utama di Sprint 5.
3. **Frontend Engineer** bisa mulai parallel dengan Backend di Sprint 1 — mock API bisa digunakan selama backend belum siap.
4. **QA Engineer** mulai aktif di Sprint 1 (test strategy & scaffolding) dan menulis tests untuk setiap sprint — tidak menunggu fitur selesai.
5. **pyrightconfig.json** sudah merencanakan `backend/` dan `worker/` direktori — pastikan struktur ini dijalankan.
6. Semua dependensi Python baru ditambahkan ke `requirements.txt`; dependensi frontend ke `package.json`.
7. Python style: type hints wajib; hindari komentar inline yang tidak perlu; docstring opsional untuk public API.
8. QA Engineer bertanggung jawab untuk memastikan **Definition of Done** terpenuhi sebelum setiap fitur dianggap selesai.
