# Sprint & Task Status — Evidentra Platform

Dokumen ini mencatat progres implementasi per sprint dan task, mengacu pada [`PROJECT_SCENARIO.md`](PROJECT_SCENARIO.md).

| Legenda | Arti |
|---|---|
| ✅ | Selesai |
| 🟡 | Parsial / MVP (fungsi inti ada, ada gap) |
| ❌ | Belum dikerjakan |

**Terakhir diperbarui:** 7 Agustus 2026  
**Integration tests:** 45 passing (`pytest tests/`)  
**Branch:** `develop`

---

## Ringkasan per Sprint

| Sprint | Fokus | Status | Progress |
|---|---|---|---|
| Sprint 1 | Foundation & WhatsApp Intelligence (d.5) | 🟡 Parsial | ~45% |
| Sprint 2 | Tactical Operations Part 1 (d.6.1–d.6.4) | ✅ Selesai (backend) | ~95% |
| Sprint 3 | Tactical Ops Part 2 + Evidence Part 1 | ✅ Selesai | ~100% |
| Sprint 4 | Digital Evidence Part 2 (d.7.3–d.7.8) | ✅ Selesai (backend) | ~90% |
| Sprint 5 | Strategic Intelligence Part 1 (d.8.1–d.8.3) | 🟡 Parsial (MVP) | ~85% |
| Sprint 6 | Integration & Testing (d.8.4) | 🟡 Parsial | ~80% |

---

## Sprint 1 — Foundation & WhatsApp Intelligence

**Tujuan:** Menyelesaikan d.5 WhatsApp Intelligence dan fondasi arsitektur platform.

| ID | Task | Modul | Status | Catatan |
|---|---|---|---|---|
| T-1.1 | WhatsApp Data Acquisition | d.5.1 | 🟡 | Script extractor ada di `extractors/whatsapp_extractor/`. `POST /api/v1/whatsapp/import` masih **stub**. Belum impor `msgstore.db` ke database. |
| T-1.2 | Communication Profile Analyzer | d.5.2 | ❌ | `backend/modules/d5_whatsapp/profile_analyzer.py` kosong. API profil belum ada. |
| T-1.3 | AI Context Mapping | d.5.3 | ❌ | `context_mapper.py` kosong. `POST /whatsapp/context-mapping` belum ada. |
| T-1.4 | Search, Filter & Insight Reporting | d.5.4 | ❌ | `search_engine.py` kosong. Endpoint search/conversations/messages belum ada. |
| T-1.5 | Database Schema Design | — | ✅ | Model SQLAlchemy, `docs/evidentra.dbml`, `docs/DATABASE_SCHEMA.md` |
| T-1.6 | Project Scaffold | — | ✅ | Struktur `backend/`, `ml/`, `worker/`, `modules/d5–d8/`, `tests/` |

**Deliverable Sprint 1**

| Deliverable | Status |
|---|---|
| Kode WhatsApp extractor terstruktur | ✅ (CLI di `extractors/`) |
| Integrasi extractor ke platform API | ❌ |
| Schema database WhatsApp & metadata | ✅ |
| Pencarian, filter, insight reporting | ❌ |

---

## Sprint 2 — Tactical Operations & Case Platform (Part 1)

**Tujuan:** Inti manajemen kasus dan operasi penyidikan.

| ID | Task | Modul | Status | Catatan |
|---|---|---|---|---|
| T-2.1 | Case Registration | d.6.1 | ✅ | `POST/GET/PUT/PATCH /cases`, metadata prioritas & assignee |
| T-2.2 | Investigation Dashboard | d.6.2 | 🟡 | API `GET /dashboard` ✅. UI visual frontend belum ada. |
| T-2.3 | Task Assignment Module | d.6.3 | ✅ | CRUD tugas, assignee, urgency, checklist, due date |
| T-2.4 | Kanban Workflow Tracking | d.6.4 | ✅ | `GET /cases/{id}/kanban`, `PATCH /tasks/{id}/move` |
| T-2.5 | API Layer | — | ✅ | FastAPI REST + Swagger `/api/docs` |
| T-2.6 | Authentication Scaffold | — | ✅ | JWT login/refresh/logout, `GET /auth/me`, admin-only user provisioning |

**Deliverable Sprint 2**

| Deliverable | Status |
|---|---|
| REST API kasus & tugas | ✅ |
| Dashboard investigasi (data real-time) | 🟡 API saja |
| Papan Kanban | ✅ |
| Auth scaffold untuk RBAC | ✅ |

**Tests:** `tests/test_auth.py`, `tests/test_cases.py`, `tests/test_users.py`

---

## Sprint 3 — Tactical Operations (Part 2) + Evidence (Part 1)

**Tujuan:** Menyelesaikan d.6 dan memulai d.7.

| ID | Task | Modul | Status | Catatan |
|---|---|---|---|---|
| T-3.1 | Organizational Hierarchy Portal | d.6.5 | ✅ | `GET/POST/PATCH /organization/hierarchy` |
| T-3.2 | Identity & Access Management (RBAC) | d.6.6 | ✅ | Role admin/investigator/viewer, `POST /users` (admin only) |
| T-3.3 | System Audit & Logging | d.6.7 | ✅ | `GET /audit-logs`, `log_activity()` di services |
| T-3.4 | Report Generation Engine (PDF) | d.6.8 | ✅ | `GET /cases/{id}/report` (ReportLab) |
| T-3.5 | Central Evidence Repository | d.7.1 | ✅ | `GET/POST/PATCH /evidence` + filter case/kategori/lokasi |
| T-3.6 | Evidence Registration Module | d.7.2 | ✅ | Metadata lengkap: IMEI, serial, GPS, storage, kondisi |

**Deliverable Sprint 3**

| Deliverable | Status |
|---|---|
| RBAC + hierarki organisasi | ✅ |
| Audit log read-only | ✅ |
| Laporan PDF kasus | ✅ |
| Evidence repository & registrasi | ✅ |

**Tests:** `tests/test_sprint3.py`

---

## Sprint 4 — Digital Evidence Management (Part 2)

**Tujuan:** Chain of Custody dan integritas bukti.

| ID | Task | Modul | Status | Catatan |
|---|---|---|---|---|
| T-4.1 | Evidence Custody & Transfer Tracking | d.7.3 | ✅ | `GET /evidence/{id}/custody`, log otomatis saat registrasi |
| T-4.2 | Evidence Transfer Approval | d.7.4 | ✅ | `POST /evidence/{id}/transfer`, `PATCH /evidence/transfers/{id}/approve` |
| T-4.3 | Evidence Integrity Verification | d.7.5 | 🟡 | SHA-256 dari metadata bukti. Hash file fisik & worker async belum. |
| T-4.4 | Asset Vault Registry | d.7.6 | ✅ | `GET /evidence/vault` |
| T-4.5 | Custody Report Generator (BAST) | d.7.7 | ✅ | `GET /evidence/{id}/custody-report` (PDF) |
| T-4.6 | Geospatial Evidence Tracking | d.7.8 | 🟡 | API `GET /evidence/geospatial` ✅. Peta visual (Leaflet) belum. |

**Deliverable Sprint 4**

| Deliverable | Status |
|---|---|
| Chain of Custody + approval workflow | ✅ |
| SHA-256 integrity verification | 🟡 |
| BAST report generator | ✅ |
| Geospatial tracking | 🟡 API saja |

**Tests:** `tests/test_sprint4.py`

---

## Sprint 5 — Strategic Intelligence & Correlation (Part 1)

**Tujuan:** Modul kecerdasan strategis dan korelasi data.

| ID | Task | Modul | Status | Catatan |
|---|---|---|---|---|
| T-5.1 | Neural Document Correlation (NER) | d.8.1 | 🟡 | `POST /intelligence/ner` — CSV/PDF. Regex default; spaCy opsional. |
| T-5.2 | Relationship Link Analysis | d.8.2 | 🟡 | `POST /intelligence/graph` — nodes/edges JSON. Visualisasi UI belum. |
| T-5.3 | APK Static Analysis Inspector | d.8.3 | 🟡 | `POST /intelligence/apk-analysis` — zipfile + androguard fallback. |
| T-5.4 | ML/AI Pipeline Infrastructure | — | 🟡 | `ml/pipeline/inference.py` + cache in-memory. Celery worker tasks kosong. |

**Deliverable Sprint 5**

| Deliverable | Status |
|---|---|
| NER engine CSV/PDF | 🟡 |
| Graph analytics | 🟡 |
| APK static analysis | 🟡 |
| ML pipeline infrastructure | 🟡 |

**Tests:** `tests/test_sprint5.py`

---

## Sprint 6 — Strategic Intelligence (Part 2) + Integration & Testing

**Tujuan:** Menyelesaikan d.8 dan integrasi lintas modul.

| ID | Task | Modul | Status | Catatan |
|---|---|---|---|---|
| T-6.1 | Advanced Analysis Dashboard | d.8.4 | ✅ | `GET /intelligence/dashboard` — metrik, job status, latency, cache TTL |
| T-6.2 | Cross-Module Integration | — | 🟡 | `GET/POST /cases/{id}/integration` & `/analyze` ✅. Import WhatsApp nyata belum terhubung. |
| T-6.3 | End-to-End Testing | — | 🟡 | `tests/test_sprint6.py` ✅. E2E pakai seed WA manual, bukan import API. |
| T-6.4 | Performance Optimization | — | 🟡 | Dashboard TTL cache, index `documents.case_id`. Optimasi query terbatas. |
| T-6.5 | Documentation & API Docs | — | 🟡 | README, API_SPEC, ARCHITECTURE, Swagger ✅. User guide belum. |

**Deliverable Sprint 6**

| Deliverable | Status |
|---|---|
| Advanced Analysis Dashboard | ✅ |
| Integrasi lintas modul | 🟡 |
| Hasil pengujian integrasi | 🟡 |
| Dokumentasi teknis | 🟡 |

**Tests:** `tests/test_sprint6.py`

---

## Status per Modul (d.5 – d.8)

| Modul | Kode | Status | Progress |
|---|---|---|---|
| WhatsApp Intelligence | d.5 | ❌ / 🟡 | ~20% — extractor CLI ada, platform API belum |
| Tactical Operations | d.6 | ✅ | ~95% — backend lengkap, UI belum |
| Digital Evidence | d.7 | ✅ | ~90% — API lengkap, peta & hash file parsial |
| Strategic Intelligence | d.8 | 🟡 | ~85% — API MVP, worker & visualisasi belum |

---

## API Endpoint — Status Implementasi

### d.5 WhatsApp (belum lengkap)

| Method | Endpoint | Status |
|---|---|---|
| POST | `/api/v1/whatsapp/import` | ❌ Stub |
| GET | `/api/v1/whatsapp/import/{import_id}` | ❌ |
| GET | `/api/v1/whatsapp/conversations` | ❌ |
| GET | `/api/v1/whatsapp/conversations/{id}/messages` | ❌ |
| GET | `/api/v1/whatsapp/profiles/{id}/summary` | ❌ |
| POST | `/api/v1/whatsapp/context-mapping` | ❌ |
| GET | `/api/v1/whatsapp/search` | ❌ |

### d.6 Tactical Operations

| Method | Endpoint | Status |
|---|---|---|
| POST | `/api/v1/auth/login` | ✅ |
| GET | `/api/v1/auth/me` | ✅ |
| POST | `/api/v1/auth/refresh` | ✅ |
| POST | `/api/v1/auth/logout` | ✅ |
| GET/POST/PATCH/DELETE | `/api/v1/users` | ✅ |
| GET/POST/PUT/PATCH | `/api/v1/cases` | ✅ |
| GET | `/api/v1/cases/{id}/summary` | ✅ |
| GET | `/api/v1/cases/{id}/kanban` | ✅ |
| GET | `/api/v1/cases/{id}/report` | ✅ |
| GET/POST | `/api/v1/cases/{id}/tasks` | ✅ |
| PATCH | `/api/v1/tasks/{id}/move` | ✅ |
| GET | `/api/v1/dashboard` | ✅ |
| GET/POST/PATCH | `/api/v1/organization/hierarchy` | ✅ |
| GET | `/api/v1/audit-logs` | ✅ |
| GET | `/api/v1/cases/{id}/integration` | ✅ |
| POST | `/api/v1/cases/{id}/analyze` | ✅ |

### d.7 Digital Evidence

| Method | Endpoint | Status |
|---|---|---|
| GET/POST/PATCH | `/api/v1/evidence` | ✅ |
| GET | `/api/v1/evidence/{id}/custody` | ✅ |
| POST | `/api/v1/evidence/{id}/transfer` | ✅ |
| PATCH | `/api/v1/evidence/transfers/{id}/approve` | ✅ |
| GET/POST | `/api/v1/evidence/{id}/integrity` | ✅ |
| GET | `/api/v1/evidence/vault` | ✅ |
| GET | `/api/v1/evidence/{id}/custody-report` | ✅ |
| GET | `/api/v1/evidence/geospatial` | ✅ |

### d.8 Strategic Intelligence

| Method | Endpoint | Status |
|---|---|---|
| POST | `/api/v1/intelligence/ner` | ✅ |
| POST | `/api/v1/intelligence/graph` | ✅ |
| POST | `/api/v1/intelligence/apk-analysis` | ✅ |
| GET | `/api/v1/intelligence/dashboard` | ✅ |

---

## Infrastruktur & Non-Functional

| Item | Status | Catatan |
|---|---|---|
| Alembic database migration | ❌ | `alembic/versions/` masih `pass`; startup pakai `create_all` |
| Celery worker tasks | ❌ | `worker/tasks/*.py` sebagian besar kosong |
| Frontend (React + Vite) | ❌ | Scaffold ada, `App.tsx` kosong |
| Docker Compose (full stack) | 🟡 | File di `infra/docker/`, belum divalidasi E2E |
| PostgreSQL (produksi) | 🟡 | Konfigurasi ada, dev pakai SQLite |
| File upload / MinIO | ❌ | `STORAGE_PATH` dikonfigurasi, upload API belum |
| CI/CD (GitHub Actions) | ❌ | Belum ada workflow |

---

## Definition of Done — Checklist Global

| Kriteria | Status |
|---|---|
| Kode implementasi mengikuti konvensi proyek | ✅ (Sprint 2–6 backend) |
| Unit tests per fitur | 🟡 Terbatas |
| Integration tests passing | ✅ 45 tests |
| Database migration tersedia | ❌ |
| API documentation diperbarui | ✅ Swagger + `API_SPECIFICATION.md` |
| Code review tim | ❓ Di luar repo |
| Tidak ada bug critical/high terbuka | ❓ Belum diaudit formal |

---

## Backlog Prioritas (belum masuk sprint resmi)

| Prioritas | Item | Modul |
|---|---|---|
| P0 | WhatsApp Import API + conversations/messages | d.5.1 |
| P0 | Alembic migration proper | Infrastruktur |
| P1 | WhatsApp profile analyzer & search | d.5.2, d.5.4 |
| P1 | Frontend MVP (login, dashboard, cases) | Frontend |
| P1 | Celery worker untuk import & hashing async | Worker |
| P2 | WhatsApp context mapping (AI) | d.5.3 |
| P2 | Geospatial map UI (Leaflet) | d.7.8 |
| P2 | Graph visualization UI | d.8.2 |
| P2 | File upload evidence & dokumen NER | d.7, d.8 |
| P3 | CI/CD pipeline | Infrastruktur |
| P3 | User guide / panduan operasional | Dokumentasi |

---

## Referensi

- [PROJECT_SCENARIO.md](PROJECT_SCENARIO.md) — rencana sprint & task asli
- [API_SPECIFICATION.md](API_SPECIFICATION.md) — spesifikasi endpoint
- [ARCHITECTURE.md](ARCHITECTURE.md) — arsitektur sistem
- [TEST_PLAN.md](TEST_PLAN.md) — strategi pengujian
- [README.md](../README.md) — status implementasi ringkas
