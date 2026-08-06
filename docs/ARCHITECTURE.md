# Architecture Design Document — Evidentra Platform

## Versi Dokumen

| Properti | Nilai |
|---|---|
| **Versi** | 1.0 |
| **Tanggal** | 2026-08-05 |
| **Penulis** | Tim Cyber |
| **Status** | Draft |

---

## 1. Gambaran Umum Arsitektur

Evidentra menggunakan arsitektur **modular monolith** dengan pemisahan lapisan yang jelas:

- **API Layer** — FastAPI REST API
- **Application Layer** — Business logic per sub-modul
- **Data Layer** — PostgreSQL + SQLite
- **Worker Layer** — Celery background tasks
- **Cache Layer** — Redis
- **Frontend Layer** — React/Vue SPA (opsional)

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (SPA)                        │
│              React / Vue + Tailwind CSS                  │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP/REST
┌──────────────────────▼──────────────────────────────────┐
│                   API Gateway (FastAPI)                  │
│              JWT Auth + RBAC Middleware                  │
│              Pydantic Validation                         │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│                  Application Layer                       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │  d.5      │ │  d.6      │ │  d.7      │ │  d.8      │  │
│  │ WhatsApp  │ │ Case Mgmt │ │ Evidence  │ │ Intelligence│  │
│  │ Intelligence│ │ Ops       │ │ Mgmt      │ │ & Correlation│  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘  │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│                    Data Layer                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ PostgreSQL    │  │ SQLite       │  │ Redis        │  │
│  │ (Produksi)    │  │ (Dev/WhatsApp│  │ (Cache &     │  │
│  │               │  │  Extraction) │  │  Celery Broker)│ │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│                  Worker Layer (Celery)                    │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐          │
│  │ SHA-256    │ │ NER        │ │ APK        │          │
│  │ Hashing    │ │ Inference  │ │ Analysis   │          │
│  │            │ │ Graph      │ │            │          │
│  │            │ │ Analytics  │ │            │          │
│  └────────────┘ └────────────┘ └────────────┘          │
└─────────────────────────────────────────────────────────┘
```

---

## 2. Komponen Utama

### 2.1 API Layer (FastAPI)

- REST API dengan otentikasi JWT
- Validasi request/response menggunakan Pydantic v2
- Dokumentasi otomatis Swagger UI di `/api/docs`
- Rate limiting untuk perlindungan API
- CORS configuration untuk frontend

### 2.2 Application Layer

Setiap sub-modul (d.5–d.8) dipisah menjadi modul independen:

| Modul | Path | Tanggung Jawab |
|---|---|---|
| d.5 WhatsApp Intelligence | `modules/d5_whatsapp/` | Parsing, analisis profil, AI context mapping, pencarian |
| d.6 Tactical Operations | `modules/d6_operations/` | Case management, task assignment, Kanban, RBAC, audit |
| d.7 Digital Evidence | `modules/d7_evidence/` | Repository, custody tracking, integrity verification, BAST |
| d.8 Strategic Intelligence | `modules/d8_intelligence/` | NER, graph analytics, APK analysis, dashboard metrics |

### 2.3 Data Layer

#### PostgreSQL (Produksi)
- Database utama untuk data kasus, tugas, pengguna, bukti, audit log
- Skema dinormalisasi dengan foreign key constraints
- Mendukung transaksi ACID
- Indexing untuk query kompleks

#### SQLite (Dev/WhatsApp Extraction)
- Digunakan untuk parsing database WhatsApp (`msgstore.db`)
- Juga digunakan sebagai database dev/testing
- Tidak digunakan di produksi

#### Redis
- Cache untuk dashboard real-time (`GET /api/v1/dashboard`)
- Broker untuk Celery task queue
- Session storage untuk JWT refresh token revocation list

#### MinIO (Produksi)
- Object storage untuk file bukti digital, dokumen NER, dan APK
- Metadata file disimpan di PostgreSQL (`documents.file_url`)
- Development menggunakan filesystem lokal (`STORAGE_PATH`)

### 2.4 Worker Layer (Celery)

Menangani tugas berat yang tidak boleh memblokir API:

| Task | Sub-Modul | Deskripsi |
|---|---|---|
| SHA-256 Hashing | d.7.5 | Perhitungan hash untuk integritas bukti |
| NER Inference | d.8.1 | Ekstraksi entitas dari dokumen |
| Graph Analytics | d.8.2 | Analisis dan visualisasi graf |
| APK Analysis | d.8.3 | Parsing dan analisis statis APK |
| PDF Report Generation | d.6.8, d.7.7 | Pembuatan laporan PDF |

### 2.5 Frontend Layer (Opsional)

- React 18+ atau Vue 3 dengan TypeScript
- Dashboard real-time menggunakan WebSocket atau polling
- Visualisasi graf (React Flow / Cytoscape.js)
- Peta interaktif (Leaflet / Mapbox GL JS)

---

## 3. Alur Data

### 3.1 Alur WhatsApp Intelligence (d.5)

```
WhatsApp Backup (msgstore.db)
        │
        ▼
[WhatsApp Extractor] ──► SQLite Parsing
        │
        ▼
[Import API] ──► POST /api/v1/whatsapp/import (Celery)
        │
        ▼
[Data Validation] ──► Validasi data percakapan
        │
        ▼
[Data Storage] ──► PostgreSQL (tabel whatsapp_data)
        │
        ▼
[Analysis Pipeline]
   ├── Communication Profile Analyzer (d.5.2)
   ├── AI Context Mapping (d.5.3) ──► NLP/LLM
   └── Search & Filter (d.5.4) ──► Full-text index
```

### 3.2 Alur Digital Evidence Management (d.7)

```
Evidence Received
        │
        ▼
[Evidence Registration (d.7.2)] ──► Metadata + SHA-256 hash
        │
        ▼
[Central Repository (d.7.1)] ──► Storage by case & category
        │
        ▼
[Custody Tracking (d.7.3)] ──► History of holders
        │
        ▼
[Transfer Approval (d.7.4)] ──► Two-party confirmation
        │
        ▼
[Integrity Verification (d.7.5)] ──► SHA-256 re-check
        │
        ▼
[BAST Report (d.7.7)] ──► PDF generation
        │
        ▼
[Geospatial Tracking (d.7.8)] ──► GPS coordinates
```

### 3.3 Alur Strategic Intelligence (d.8)

```
Input Data (CSV/PDF/APK)
        │
        ▼
[Document Correlation (d.8.1)] ──► NER → Entities extracted
        │
        ▼
[Relationship Analysis (d.8.2)] ──► Graph construction → Visualization
        │
        ▼
[APK Analysis (d.8.3)] ──► Static parsing → Threat indicators
        │
        ▼
[Dashboard (d.8.4)] ──► Metrics, status, latency, results
```

---

## 4. Keamanan Arsitektur

| Aspek | Implementasi |
|---|---|
| Autentikasi | JWT dengan akses token + refresh token |
| Otorisasi | RBAC (Role-Based Access Control) |
| Data Integrity | SHA-256 hashing untuk bukti digital |
| Audit Trail | Log read-only untuk semua aktivitas pengguna |
| Transport Security | HTTPS/TLS untuk semua komunikasi API |
| Input Validation | Pydantic schema validation untuk semua request |
| SQL Injection | SQLAlchemy ORM (parameterized queries) |
| Rate Limiting | FastAPI rate limiter untuk perlindungan API |

---

## 5. Deployment Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Deployment                            │
│                                                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │  Frontend    │  │  Backend    │  │  Celery      │    │
│  │  (Static     │  │  (FastAPI)  │  │  Workers     │    │
│  │   SPA)       │  │  Gunicorn   │  │  (Celery)    │    │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘    │
│         │                 │                  │            │
│         └────────────┬────┴──────────────────┘            │
│                      │                                    │
│              ┌───────▼────────┐                           │
│              │   Nginx        │                           │
│              │   (Reverse     │                           │
│              │    Proxy)      │                           │
│              └───────┬────────┘                           │
│                      │                                    │
│         ┌────────────┼────────────┐                      │
│         ▼            ▼            ▼                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                │
│  │PostgreSQL│ │  Redis   │ │  MinIO   │                │
│  │   15+    │ │   7+     │ │ (Storage)│                │
│  └──────────┘ └──────────┘ └──────────┘                │
└─────────────────────────────────────────────────────────┘
```

---

## 6. Skalabilitas

| Komponen | Strategi Skalabilitas |
|---|---|
| API Layer | Horizontal scaling dengan Gunicorn workers |
| Celery Workers | Horizontal scaling, tambah worker berdasarkan queue |
| PostgreSQL | Connection pooling (PgBouncer), read replicas |
| Redis | Redis Cluster untuk high availability |
| Storage | MinIO untuk object storage yang scalable |
| Frontend | CDN untuk static assets |
