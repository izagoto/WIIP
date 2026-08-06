# Evidentra Digital Forensics & Intelligence Platform

Platform perangkat lunak forensik digital terintegrasi untuk operasi penegakan hukum, dikembangkan sebagai bagian dari proyek **Digifor Brimob**.

## Tentang Proyek

Evidentra adalah platform terpusat yang menyediakan modul akuisisi data, WhatsApp Intelligence, manajemen kasus penyidikan, manajemen barang bukti digital, dan analisis kecerdasan strategis. Platform ini dirancang untuk mendukung kegiatan forensik digital di lapangan maupun di pusat.

## Struktur Proyek

```
brimob_forensiq/
├── backend/                    # FastAPI backend application (Backend Engineer)
│   ├── main.py                 # FastAPI app entry point
│   ├── api/                    # API routes & endpoints (v1)
│   │   ├── v1/
│   │   │   ├── auth.py
│   │   │   ├── whatsapp.py
│   │   │   ├── cases.py
│   │   │   ├── tasks.py
│   │   │   ├── evidence.py
│   │   │   ├── intelligence.py
│   │   │   └── dashboard.py
│   │   └── deps.py
│   ├── models/                 # SQLAlchemy ORM models
│   ├── schemas/                # Pydantic request/response schemas
│   ├── services/               # Business logic services
│   ├── core/                   # Shared utilities (config, DB, auth, logging)
│   ├── middleware/             # FastAPI middleware (auth, RBAC, audit)
│   └── modules/                # Domain-specific business logic
│       ├── d5_whatsapp/
│       ├── d6_operations/
│       ├── d7_evidence/
│       └── d8_intelligence/
├── worker/                     # Celery background workers (Backend Engineer)
│   ├── celery_app.py
│   └── tasks/
├── ml/                         # ML/AI models & pipelines (ML/AI Specialist)
│   ├── ner/
│   ├── graph/
│   ├── apk/
│   ├── pipeline/
│   └── utils/
├── frontend/                   # React/Vue SPA (Frontend Engineer)
│   ├── public/
│   └── src/
│       ├── components/
│       ├── pages/
│       ├── hooks/
│       ├── services/
│       ├── store/
│       ├── types/
│       └── utils/
├── extractors/                 # Data extraction tools (existing)
│   └── whatsapp_extractor/
├── tests/                      # All tests (QA Engineer)
│   ├── unit/
│   ├── integration/
│   ├── e2e/
│   ├── fixtures/
│   └── factories/
├── data/                       # Data files
│   ├── raw_evidence/
│   ├── raw_whatsapp_data/
│   ├── processed/
│   └── exports/
├── docs/                       # Documentation
├── infra/                      # Infrastructure configs (Docker, nginx, alembic)
├── scripts/                    # Utility & dev scripts
├── backend/
├── worker/
├── ml/
├── frontend/
├── tests/
├── infra/
├── scripts/
├── .env.example
├── .gitignore
├── pyrightconfig.json
├── requirements.txt            # Base dependencies (extractors)
├── requirements-ml.txt         # ML/AI dependencies
├── requirements-dev.txt        # Dev/testing dependencies
└── README.md
```

## Peran & Direktori

| Peran | Direktori Utama |
|---|---|
| **Backend Engineer** | `backend/`, `worker/` |
| **ML/AI Specialist** | `ml/` |
| **Frontend Engineer** | `frontend/` |
| **QA Engineer** | `tests/` |

## Sub-Modul

| Kode | Modul | Direktori |
|---|---|---|
| d.5 | WhatsApp Intelligence | `backend/modules/d5_whatsapp/` |
| d.6 | Tactical Operations | `backend/modules/d6_operations/` |
| d.7 | Digital Evidence Management | `backend/modules/d7_evidence/` |
| d.8 | Strategic Intelligence | `backend/modules/d8_intelligence/` |

## Teknologi Utama

- **Python 3.11+** — bahasa utama
- **FastAPI** — web framework untuk REST API
- **SQLAlchemy 2.0** — ORM
- **PostgreSQL** — database produksi
- **Celery + Redis** — background tasks & caching
- **Protocol Buffers** — serialisasi data WhatsApp crypto

## Instalasi

### Prasyarat

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Node.js 18+ (untuk frontend)

### Setup Environment

```bash
# Backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-ml.txt
pip install -r requirements-dev.txt

# Frontend
cd frontend
npm install
```

### Menjalankan

```bash
# Backend
uvicorn backend.main:app --reload

# Worker (Celery)
celery -A worker.celery_app worker --loglevel=info

# Frontend
cd frontend
npm run dev
```

## Lisensi

Proyek ini bersifat internal dan untuk kepentingan operasional Brimob.
