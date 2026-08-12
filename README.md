# Evidentra

**Digital Forensics & Intelligence Platform** — proyek **Digifor Brimob**

Platform terpusat untuk akuisisi data digital, analisis komunikasi WhatsApp, manajemen kasus penyidikan, rantai kustodi barang bukti, dan korelasi intelijen strategis. Dirancang untuk operasi forensik digital di lapangan maupun di pusat, dengan penekanan pada keutuhan data, jejak audit, dan kontrol akses berbasis peran.

---

## Modul Platform


| Kode    | Modul                       | Ringkasan                                                                          |
| ------- | --------------------------- | ---------------------------------------------------------------------------------- |
| **d.5** | WhatsApp Intelligence       | Impor, profil komunikasi, pencarian pesan, dan pemetaan konteks percakapan         |
| **d.6** | Tactical Operations         | IAM, manajemen kasus, tugas Kanban, hierarki organisasi, dan audit log             |
| **d.7** | Digital Evidence Management | Registrasi bukti, kustodi, transfer, verifikasi integritas SHA-256, dan geospasial |
| **d.8** | Strategic Intelligence      | NER dokumen, analisis graf relasi, inspeksi APK, dan dashboard intelijen           |


Spesifikasi lengkap modul mengacu pada dokumen sumber di `[docs/Solution_Pack_Digifor_Brimob.pdf](docs/Solution_Pack_Digifor_Brimob.pdf)` dan `[docs/Spectek_Digital_Forensics_Intelligence_Module.pdf](docs/Spectek_Digital_Forensics_Intelligence_Module.pdf)`.

---

## Status Implementasi


| Sprint       | Cakupan                                                            | Status  |
| ------------ | ------------------------------------------------------------------ | ------- |
| **Sprint 1** | Foundation — auth JWT, model database, migrasi, seed, health check | Selesai |
| **Sprint 2** | Case platform API — kasus, tugas, Kanban, dashboard, RBAC          | Selesai |
| **Sprint 3** | Org hierarchy, audit logs, laporan PDF kasus, evidence repository  | Selesai |
| **Sprint 4** | Custody, transfer approval, SHA-256, vault, BAST, geospatial       | Selesai |
| **Sprint 5** | NER dokumen, analisis graf relasi, APK inspector, ML pipeline      | Selesai |
| **Sprint 6** | Dashboard intelijen, integrasi lintas modul, pengujian E2E         | Selesai |


### Ringkasan API per Sprint


| Sprint | Endpoint utama                                                                                                                                                                                                                                 |
| ------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **1**  | `POST /auth/login`, `GET /auth/me`, `POST /auth/refresh`, `POST /auth/logout`, `GET /health`                                                                                                                                                   |
| **2**  | `CRUD /cases`, `CRUD /tasks`, `PATCH /tasks/{id}/status`, `GET /dashboard/summary`, `CRUD /users` (admin)                                                                                                                                      |
| **3**  | `CRUD /organization/hierarchy`, `GET /audit-logs`, `GET /cases/{id}/report` (PDF), `CRUD /evidence`                                                                                                                                            |
| **4**  | `GET /evidence/{id}/custody`, `POST /evidence/{id}/transfer`, `PATCH /evidence/transfers/{id}/approve`, `GET|POST /evidence/{id}/integrity`, `GET /evidence/vault`, `GET /evidence/{id}/custody-report` (BAST PDF), `GET /evidence/geospatial` |
| **5**  | `POST /intelligence/ner`, `POST /intelligence/graph`, `POST /intelligence/apk-analysis`, `GET /intelligence/dashboard`                                                                                                                         |
| **6**  | `GET /cases/{id}/integration`, `POST /cases/{id}/analyze`, dashboard intelijen lanjutan (cache TTL), alur E2E lintas modul                                                                                                                     |


**Pengujian:** 45 integration tests (`pytest tests/`) — mencakup Sprint 1–6 termasuk alur E2E.

Detail status per task dan endpoint: `[docs/SPRINT_STATUS.md](docs/SPRINT_STATUS.md)`.

API yang sudah tersedia dapat diuji melalui Swagger UI di `[/api/docs](http://localhost:8000/api/docs)`. Riwayat perubahan terperinci ada di `[docs/CHANGELOG.md](docs/CHANGELOG.md)`.

---

## Prasyarat

- Python 3.11+
- PostgreSQL 15+ (produksi) — SQLite untuk development lokal
- Redis 7+ (worker & cache)
- Node.js 18+ (frontend, opsional)

---

## Menjalankan (Development)

```bash
# 1. Virtual environment & dependensi
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Konfigurasi environment (file di root proyek)
cp .env.example .env
# Edit .env — set SEED_ADMIN_* dan SEED_INVESTIGATOR_* untuk bootstrap user

# 3. Migrasi database
alembic upgrade head

# 4. Backend API
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Saat startup, aplikasi otomatis membuat tabel database dan menjalankan seed (jika `SEED_ON_STARTUP=true` dan `ENVIRONMENT=development`). Seed manual: `python scripts/seed.py`.


| Endpoint     | URL                                                              |
| ------------ | ---------------------------------------------------------------- |
| Swagger UI   | [http://localhost:8000/api/docs](http://localhost:8000/api/docs) |
| Health check | [http://localhost:8000/health](http://localhost:8000/health)     |


**Kebijakan autentikasi:** tidak ada registrasi publik. Akun admin bootstrap via seed; admin menambahkan investigator dan viewer melalui `POST /api/v1/users`.

---

## Dokumentasi

Seluruh dokumentasi teknis dan operasional berada di direktori `[docs/](docs/)`.

### Skenario & Konteks Bisnis


| Dokumen                                             | Deskripsi                                                          |
| --------------------------------------------------- | ------------------------------------------------------------------ |
| `[PROJECT_SCENARIO.md](docs/PROJECT_SCENARIO.md)`   | Skenario eksekusi proyek, tujuan, dan ruang lingkup Digifor Brimob |
| `[SISTEM_SCENARIO.md](docs/SISTEM_SCENARIO.md)`     | Alur sistem end-to-end, aktor, dan interaksi antar modul           |
| `[ROLE_REQUIREMENTS.md](docs/ROLE_REQUIREMENTS.md)` | Kebutuhan peran tim (Backend, ML/AI, Frontend, QA) per sprint      |


### Arsitektur & Spesifikasi Teknis


| Dokumen                                             | Deskripsi                                                                 |
| --------------------------------------------------- | ------------------------------------------------------------------------- |
| `[ARCHITECTURE.md](docs/ARCHITECTURE.md)`           | Desain arsitektur modular monolith, lapisan komponen, dan alur data       |
| `[API_SPECIFICATION.md](docs/API_SPECIFICATION.md)` | Spesifikasi REST API (`/api/v1`), konvensi enum, request/response         |
| `[DATABASE_SCHEMA.md](docs/DATABASE_SCHEMA.md)`     | Skema database, relasi entitas, indeks, dan panduan migrasi Alembic       |
| `[evidentra.dbml](docs/evidentra.dbml)`             | Diagram ERD (DBML) untuk import ke [dbdiagram.io](https://dbdiagram.io/d) |


### Keamanan & Operasional


| Dokumen                               | Deskripsi                                                               |
| ------------------------------------- | ----------------------------------------------------------------------- |
| `[SECURITY.md](docs/SECURITY.md)`     | Kebijakan keamanan, klasifikasi data, JWT, RBAC, dan rate limiting      |
| `[DEPLOYMENT.md](docs/DEPLOYMENT.md)` | Panduan deployment Docker, konfigurasi server, dan environment produksi |
| `[TEST_PLAN.md](docs/TEST_PLAN.md)`   | Strategi pengujian unit, integrasi, E2E, performa, dan keamanan         |


### AI On-Premise


| Dokumen                                                     | Deskripsi                                                   |
| ----------------------------------------------------------- | ----------------------------------------------------------- |
| `[AI_TECHNICAL_ANALYSIS.md](docs/AI_TECHNICAL_ANALYSIS.md)` | Analisis teknis implementasi AI lokal untuk d.5.3 dan d.8.1 |
| `[AI_INSTALL_MINI_PC.md](docs/AI_INSTALL_MINI_PC.md)`       | Panduan instalasi stack AI on-premise di perangkat Mini PC  |


### Pengembangan


| Dokumen                                               | Deskripsi                                                           |
| ----------------------------------------------------- | ------------------------------------------------------------------- |
| `[CONTRIBUTING.md](docs/CONTRIBUTING.md)`             | Alur kontribusi, branch strategy, standar kode, dan proses review   |
| `[SPRINT_STATUS.md](docs/SPRINT_STATUS.md)`           | Status implementasi per sprint, task, dan endpoint API (✅ / 🟡 / ❌) |
| `[MANUAL_WALKTHROUGH.md](docs/MANUAL_WALKTHROUGH.md)` | Panduan manual uji endpoint — skenario kasus 1 HP Android           |
| `[CHANGELOG.md](docs/CHANGELOG.md)`                   | Riwayat perubahan proyek (Keep a Changelog)                         |


---

## Stack Teknologi

Python 3.11 · FastAPI · SQLAlchemy 2.0 · PostgreSQL / SQLite · Celery · Redis · React (frontend) · Protocol Buffers (WhatsApp crypto)

Detail arsitektur dan versi dependensi: `[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)`.

---

## Lisensi

Proyek ini bersifat **internal** dan ditujukan untuk kepentingan operasional Brimob. Distribusi atau penggunaan di luar lingkup yang ditetapkan memerlukan persetujuan resmi.