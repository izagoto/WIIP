# AI Local Install Guide — MSI Mini PC

## Panduan Instalasi AI On-Premise di Mini PC MSI

| Properti | Nilai |
|---|---|
| **Target Device** | Mini PC MSI |
| **Tujuan** | Instalasi lengkap AI stack untuk d.5.3 & d.8.1 (100% offline) |
| **Dokumen Ini** | `docs/AI_INSTALL_MINI_PC.md` |
| **Tanggal** | 2026-08-06 |

---

## 1. Prasyarat & Hardware Check

### 1.1 Spesifikasi Minimal MSI Mini PC

| Komponen | Minimal | Disarankan |
|---|---|---|
| **OS** | Windows 10/11 atau Ubuntu 22.04+ | Ubuntu 22.04 LTS 64-bit |
| **CPU** | Intel i5 / AMD Ryzen 5 | Intel i7 / AMD Ryzen 7 |
| **RAM** | 16 GB | 32 GB |
| **GPU** | Integrated graphics | NVIDIA GTX 1660 / RTX 3060 (8GB+ VRAM) |
| **Storage** | 256 GB SSD | 1 TB NVMe SSD |
| **Network** | Ethernet/WiFi | Ethernet (untuk model download sekali) |

### 1.2 Cek Spesifikasi

```bash
# Linux (Ubuntu)
lscpu                    # CPU info
free -h                  # RAM
lspci | grep VGA         # GPU info
nvidia-smi               # NVIDIA GPU info (jika ada)
df -h                    # Storage
```

```powershell
# Windows
wmic cpu get name, NumberOfCores, NumberOfLogicalProcessors
wmic computersystem get TotalPhysicalMemory
# GPU: buka Task Manager → Performance → GPU
```

---

## 2. Persiapan Operating System

### 2.1 Jika menggunakan Linux (Ubuntu 22.04 — RECOMMENDED)

#### Update system

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl wget git build-essential software-properties-common
```

#### Install dependensi dasar

```bash
sudo apt install -y python3 python3-pip python3-venv python3-dev
sudo apt install -y build-essential cmake git wget
```

#### Install NVIDIA drivers (jika ada GPU NVIDIA)

```bash
# Cek GPU
lspci | grep -i nvidia

# Install NVIDIA driver
sudo apt install -y nvidia-driver-535
sudo apt install -y nvidia-utils-535

# Reboot
sudo reboot
```

#### Install NVIDIA Container Toolkit (untuk Docker GPU)

```bash
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -fsSL https://nvidia.github.io/libnvidia-container/gpg.distributions/$distribution.tar.gz | tar -xz -C /usr/share/keyrings
sudo apt update && sudo apt install -y nvidia-docker2
sudo systemctl restart docker
```

### 2.2 Jika menggunakan Windows 10/11

#### Install Windows Subsystem for Linux (WSL2) — RECOMMENDED

```powershell
# Jalankan PowerShell sebagai Administrator
wsl --install
wsl --set-default-version 2

# Install Ubuntu 22.04 dari Microsoft Store
```

#### Atau gunakan Windows Native (Python langsung)

```powershell
# Download Python 3.11+ dari https://python.org
# Pastikan "Add to PATH" tercentang
```

---

## 3. Instalasi Python Environment

### 3.1 Buat Virtual Environment

```bash
# Di dalam folder proyek
cd /opt/evidentra   # atau C:\evidentra di Windows
python3 --version   # Pastikan Python 3.11+
python3 -m venv venv
source venv/bin/activate   # Linux/Mac
# atau
.\venv\Scripts\activate    # Windows
```

### 3.2 Upgrade pip

```bash
pip install --upgrade pip setuptools wheel
```

### 3.3 Install Python Dependencies

```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
pip install transformers>=4.35.0 sentence-transformers>=3.0.0
pip install spacy>=3.7.0 faiss-cpu>=1.7.0 pdfplumber>=0.10.0
pip install pandas numpy scikit-learn>=1.3.0 requests>=2.34.0
pip install celery>=5.3.0 redis>=5.0.0 ollama>=0.1.0
```

Jika tidak ada GPU atau ingin CPU-only:

```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

---

## 4. Instalasi Ollama (LLM Engine)

### 4.1 Linux (Ubuntu)

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pastikan service berjalan
sudo systemctl status ollama

# Jika belum running:
sudo systemctl start ollama
sudo systemctl enable ollama  # auto-start setiap boot
```

### 4.2 Windows

```powershell
# Download dari https://ollama.com/download
# Install dengan .msi runner
# Bisa juga via WSL2
```

### 4.3 Konfigurasi Ollama untuk GPU (jika tersedia)

Edit file konfigurasi:

```bash
# Linux
sudo nano /etc/systemd/system/ollama.service

# Tambahkan environment variable:
Environment="OLLAMA_MODELS=/opt/evidentra/models/ollama"
Environment="HOROLLOAMA=true"   # Untuk GPU support
```

### 4.4 Test Koneksi Ollama

```bash
# Test API
curl http://localhost:11434/api/tags

# Jika berhasil, akan menampilkan JSON dengan model yang tersedia
```

---

## 5. Unduh Model AI (One-time setup)

### 5.1 Model LLM untuk d.5.3 (Ollama)

```bash
# Unduh model utama
ollama pull qwen2.5:7b-instruct-q4_K_M

# Jika ada GPU dengan 16GB+ VRAM, gunakan versi 14B
ollama pull qwen2.5:14b-instruct-q4_K_M
```

### 5.2 Model NER untuk d.8.1 (Transformers)

```bash
# Unduh model IndoBERT NER
python -c "
from transformers import AutoTokenizer, AutoModelForTokenClassification

# Unduh tokenizer dan model
tokenizer = AutoTokenizer.from_pretrained('cahya/indobert-base-p1-ner')
model = AutoModelForTokenClassification.from_pretrained('cahya/indobert-base-p1-ner')

# Simpan ke cache lokal
print('Model downloaded successfully')
print(f'Model cache: {model.save_pretrained(\"/opt/evidentra/models/indobert-ner\")}')
"
```

### 5.3 spaCy Indonesian Model

```bash
# Install spacy
pip install spacy

# Download Indonesian model
python -m spacy download id_core_news_lg

# Verifikasi
python -c "import spacy; nlp = spacy.load('id_core_news_lg'); print('spaCy id_core_news_lg loaded successfully')"
```

### 5.4 Embedding Model (BGE-M3)

```bash
# Download embedding model
python -c "
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('BAAI/bge-m3')
print('BGE-M3 model downloaded successfully')
"
```

### 5.5 Simpan Semua Model ke Direktori Khusus

```bash
mkdir -p /opt/evidentra/models/ollama
mkdir -p /opt/evidentra/models/transformers
mkdir -p /opt/evidentra/models/spacy
mkdir -p /opt/evidentra/models/embeddings
```

---

## 6. Instalasi FAISS (Vector Database)

### 6.1 FAISS CPU (untuk mini PC tanpa GPU)

```bash
pip install faiss-cpu
```

### 6.2 FAISS GPU (jika ada NVIDIA GPU)

```bash
# Pastikan CUDA toolkit terinstall
# Untuk Ubuntu:
sudo apt install -y nvidia-cuda-toolkit

# Install FAISS dengan GPU support
pip install faiss-gpu

# Test
python -c "import faiss; print('FAISS version:', faiss.__version__); print('GPU available:', faiss.get_num_gpus())"
```

---

## 7. Instalasi Redis (Cache & Celery Broker)

### 7.1 Via Docker (Recommended)

```bash
# Jika Docker sudah terinstall
docker run -d --name redis-evidentra -p 6379:6379 redis:7-alpine

# Auto-start
docker update --restart unless-stopped redis-evidentra
```

### 7.2 Via apt (Linux)

```bash
sudo apt install -y redis-server redis-tools
sudo systemctl enable redis
sudo systemctl start redis
```

### 7.3 Via MSI Installer (Windows)

Unduh dari https://github.com/microsoftarchive/redis/releases

```powershell
# Install Redis untuk Windows
# Konfigurasi port 6379
```

---

## 8. Instalasi PostgreSQL (Database)

### 8.1 Via Docker

```bash
docker run -d \
  --name postgres-evidentra \
  -e POSTGRES_USER=evidentra \
  -e POSTGRES_PASSWORD=evidentra123 \
  -e POSTGRES_DB=evidentra_db \
  -p 5432:5432 \
  -v /opt/evidentra/data/postgres:/var/lib/postgresql/data \
  postgres:15-alpine

# Auto-start
docker update --restart unless-stopped postgres-evidentra
```

### 8.2 Via apt (Linux)

```bash
sudo apt install -y postgresql postgresql-contrib
sudo systemctl enable postgresql
sudo systemctl start postgresql

# Buat database dan user
sudo -u postgres psql -c "CREATE USER evidentra WITH PASSWORD 'evidentra123';"
sudo -u postgres psql -c "CREATE DATABASE evidentra_db OWNER evidentra;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE evidentra_db TO evidentra;"
```

---

## 9. Konfigurasi Project

### 9.1 Clone Project Repository

```bash
cd /opt/evidentra
git clone <repository_url> .
```

### 9.2 Buat Environment File (.env)

```bash
cat > /opt/evidentra/.env << 'EOF'
# Database
DATABASE_URL=postgresql://evidentra:evidentra123@localhost:5432/evidentra_db

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
JWT_SECRET_KEY=$(openssl rand -base64 32)
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b-instruct-q4_K_M

# Model paths
TRANSFORMERS_CACHE=/opt/evidentra/models/transformers
SPACY_MODELS=/opt/evidentra/models/spacy
FAISS_INDEX_PATH=/opt/evidentra/models/faiss

# Environment
ENVIRONMENT=production
DEBUG=false

# Storage
STORAGE_PATH=/opt/evidentra/data/uploads

# Logging
LOG_LEVEL=INFO
EOF
```

### 9.3 Set Environment Variables

```bash
# Linux
sudo nano /etc/environment
# Tambahkan:
export OMP_NUM_THREADS=4
export MKL_NUM_THREADS=4
```

---

## 10. Instalasi dan Konfigurasi Backend

### 10.1 Install Backend Dependencies

```bash
cd /opt/evidentra
source venv/bin/activate
pip install -r requirements.txt

# Jika requirements.txt belum lengkap, install tambahan:
pip install fastapi uvicorn[standard] sqlalchemy psycopg2-binary alembic
pip install python-jose[cryptography] passlib[bcrypt] python-multipart
pip install weasyprint gunicorn
```

### 10.2 Database Migration

```bash
# Inisialisasi Alembic (jika belum ada)
alembic init alembic

# Konfigurasi alembic.ini
# Edit sqlalchemy.url = postgresql://evidentra:evidentra123@localhost:5432/evidentra_db

# Buat migrasi otomatis
alembic revision --autogenerate -m "initial_schema"

# Jalankan migrasi
alembic upgrade head
```

### 10.3 Konfigurasi Celery Worker

Buat file `worker/ai_worker.py`:

```python
import os
import spacy
from celery import Celery
from transformers import pipeline
from sentence_transformers import SentenceTransformer
import torch

# Load models once (singleton pattern)
print("Loading spaCy model...")
spacy_nlp = spacy.load("id_core_news_lg")

print("Loading NER pipeline (IndoBERT)...")
device = "cuda" if torch.cuda.is_available() else "cpu"
ner_pipeline = pipeline(
    "ner",
    model="cahya/indobert-base-p1-ner",
    tokenizer="cahya/indobert-base-p1-ner",
    device=0 if device == "cuda" else -1,
)

print("Loading embedding model (BGE-M3)...")
embedding_model = SentenceTransformer("BAAI/bge-m3", device=device)

print("Loading FAISS index...")
import faiss
# Load or create FAISS index

# Celery configuration
app = Celery("ai_worker", broker=os.environ["REDIS_URL"], backend=os.environ["REDIS_URL"])

app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Jakarta",
    enable_utc=True,
)

# Import tasks
from modules.d5_whatsapp.ai_context import process_ai_context
from modules.d8_intelligence.ner_pipeline import process_ner_document

@app.task
def health_check():
    return {
        "sparql_loaded": spacy_nlp is not None,
        "ner_loaded": ner_pipeline is not None,
        "embedding_loaded": embedding_model is not None,
        "faiss_loaded": True,
        "device": device,
    }

if __name__ == "__main__":
    app.start()
```

### 10.4 Konfigurasi Backend App

Buat file `backend/main.py`:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import ollama

app = FastAPI(title="Evidentra AI Platform", version="1.0.0")

# Test Ollama connection on startup
@app.on_event("startup")
async def startup():
    try:
        client = ollama.Client(host=os.environ["OLLAMA_HOST"])
        models = client.list()
        print(f"Connected to Ollama. Models: {[m['name'] for m in models['models']]}")
    except Exception as e:
        print(f"Ollama connection failed: {e}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.environ.get("ALLOWED_ORIGINS", "*")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import routers
from modules.d5_whatsapp.routes import router as whatsapp_router
from modules.d6_operations.routes import router as operations_router
from modules.d7_evidence.routes import router as evidence_router
from modules.d8_intelligence.routes import router as intelligence_router

app.include_router(whatsapp_router, prefix="/api/v1/whatsapp", tags=["whatsapp"])
app.include_router(operations_router, prefix="/api/v1", tags=["operations"])
app.include_router(evidence_router, prefix="/api/v1/evidence", tags=["evidence"])
app.include_router(intelligence_router, prefix="/api/v1/intelligence", tags=["intelligence"])
```

---

## 11. Instalasi Web Server

### 11.1 Backend Web Server (Gunicorn)

```bash
pip install gunicorn

# Jalankan di production
gunicorn backend.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120 \
  --keep-alive 5
```

### 11.2 Nginx Reverse Proxy

#### Linux

```bash
sudo apt install -y nginx

# Konfigurasi
sudo tee /etc/nginx/sites-available/evidentra << 'EOF'
upstream backend {
    server localhost:8000;
}

server {
    listen 80;
    server_name localhost;

    client_max_body_size 100M;

    location /api/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api/docs {
        proxy_pass http://backend;
    }
}
EOF

sudo ln -s /etc/nginx/sites-available/evidentra /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl enable nginx
sudo systemctl restart nginx
```

#### Windows

Gunakan Caddy atau IIS sebagai reverse proxy, atau jalankan FastAPI langsung:

```powershell
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## 12. Service Configuration (Systemd — Linux)

### 12.1 Backend Service

```bash
sudo tee /etc/systemd/system/evidentra-backend.service << 'EOF'
[Unit]
Description=Evidentra Backend API
After=network.target redis-server.target postgresql.target

[Service]
User=evidentra
Group=evidentra
WorkingDirectory=/opt/evidentra
Environment="ENVIRONMENT=production"
Environment="PYTHONPATH=/opt/evidentra"
ExecStart=/opt/evidentra/venv/bin/gunicorn backend.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --timeout 120
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
```

### 12.2 AI Worker Service

```bash
sudo tee /etc/systemd/system/evidentra-ai-worker.service << 'EOF'
[Unit]
Description=Evidentra AI Worker (Celery)
After=network.target redis-server.target postgresql.target ollama.service

[Service]
User=evidentra
Group=evidentra
WorkingDirectory=/opt/evidentra
Environment="ENVIRONMENT=production"
Environment="PYTHONPATH=/opt/evidentra"
Environment="OLLAMA_HOST=http://localhost:11434"
ExecStart=/opt/evidentra/venv/bin/celery -A worker.ai_worker.app worker --loglevel=info --concurrency=2
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
```

### 12.3 Aktifkan Semua Service

```bash
sudo systemctl daemon-reload
sudo systemctl enable evidentra-backend
sudo systemctl enable evidentra-ai-worker
sudo systemctl start evidentra-backend
sudo systemctl start evidentra-ai-worker
```

---

## 13. Verifikasi Instalasi

### 13.1 Cek Ollama

```bash
# Cek service berjalan
curl http://localhost:11434/api/tags

# Test inference
curl http://localhost:11434/api/generate -d '{
  "model": "qwen2.5:7b-instruct-q4_K_M",
  "prompt": "Apa ibukota Indonesia?",
  "stream": false
}'
```

### 13.2 Cek spaCy NER

```bash
python -c "
import spacy
nlp = spacy.load('id_core_news_lg')
doc = nlp('John Doe dari Jakarta bertemu dengan Jane di Bandung.')
for ent in doc.ents:
    print(ent.text, ent.label_)
# Output: John Doe PERSON, Jakarta LOCATION, Jane PERSON, Bandung LOCATION
"
```

### 13.3 Cek IndoBERT NER

```bash
python -c "
from transformers import pipeline
ner = pipeline('ner', model='cahya/indobert-base-p1-ner', tokenizer='cahya/indobert-base-p1-ner')
text = 'John Doe dari Jakarta bertemu dengan Jane di Bandung.'
result = ner(text)
for r in result:
    print(r)
"
```

### 13.4 Cek FAISS

```bash
python -c "
import faiss
import numpy as np
dimension = 1024
index = faiss.IndexFlatIP(dimension)
print('FAISS version:', faiss.__version__)
print('Index created:', index)
"
```

### 13.5 Cek Celery Worker

```bash
# Check worker running
celery -A worker.ai_worker.app inspect active

# Health check via HTTP
curl http://localhost:8000/api/v1/ai/health
```

### 13.6 Cek Web API

```bash
# Test API
curl http://localhost:8000/
curl http://localhost:8000/api/docs  # Swagger UI
```

---

## 14. Optimasi Performa Mini PC

### 14.1 Jika Tidak Ada GPU (CPU-only)

| Model | Latency CPU | Solusi |
|---|---|---|
| Qwen 2.5 7B | 10-30 detik | Gunakan Qwen 2.5 3B (lebih ringan) atau gunakan caching |
| IndoBERT NER | 5-15 detik | Pre-load model di startup, gunakan thread pool |
| spaCy NER | < 1 detik | Wajib pakai ini sebagai primary |
| BGE-M3 | 2-5 detik | Batch processing |

#### Rekomendasi untuk CPU-only:

```bash
# Pakai model yang lebih kecil
pip install llama-cpp-python  # Alternatif Ollama untuk CPU
# Atau gunakan phi-3-mini (3.8GB) via llama.cpp
```

### 14.2 Jika Ada GPU NVIDIA

```bash
# Pastikan CUDA terpasang
nvidia-smi

# Set environment variables untuk GPU
export CUDA_VISIBLE_DEVICES=0
export OMP_NUM_THREADS=4

# Konfigurasi Ollama untuk GPU
OLLAMA_MODELS=/opt/evidentra/models/ollama ollama serve
```

### 14.3 Optimasi Memory

```bash
# Batasi memory usage per worker
celery -A worker.ai_worker.app worker --loglevel=info --concurrency=2 --memory-limit=4096

# Batasi memory untuk frontend/backend
# Gunakan ulimit
ulimit -v 2097152  # 2GB virtual memory limit
```

---

## 15. Troubleshooting

### 15.1 Ollama Tidak Bisa Start

```bash
# Cek service
sudo systemctl status ollama

# Jika gagal:
sudo rm -rf /tmp/ollama*
sudo systemctl restart ollama

# Cek log
journalctl -u ollama -f
```

### 15.2 Model Tidak Berjalan (CUDA error)

```bash
# Jika menggunakan GPU dan dapat error CUDA
export CUDA_VISIBLE_DEVICES=""  # Force CPU mode
export OMP_NUM_THREADS=8        # Gunakan semua CPU core
```

### 15.3 Memory Out of Bound

```bash
# Gunakan model yang lebih kecil
ollama pull qwen2.5:3b       # 3B parameter (lebih ringan)

# Atau gunakan quantization lebih agresif
ollama pull qwen2.5:7b-instruct-q3_K_M
```

### 15.4 Port Conflict

```bash
# Cek port yang digunakan
sudo ss -tlnp | grep -E '8000|11434|6379|5432'

# Hentikan service yang bentrok
sudo systemctl stop nginx  # contoh
```

### 15.5 spaCy Model Error

```bash
# Hapus dan install ulang
python -m spacy.uninstall id_core_news_lg
python -m spacy download id_core_news_lg

# Verifikasi
python -c "import spacy; nlp = spacy.load('id_core_news_lg')"
```

---

## 16. Checklist Verifikasi Akhir

- [ ] Python 3.11+ terinstall
- [ ] Virtual environment dibuat dan activated
- [ ] PostgreSQL berjalan dan database `evidentra_db` siap
- [ ] Redis berjalan di localhost:6379
- [ ] Ollama service berjalan di localhost:11434
- [ ] Model Qwen 2.5 sudah di-download (qwen2.5:7b-instruct-q4_K_M)
- [ ] Model IndoBERT NER sudah di-download
- [ ] Model spaCy `id_core_news_lg` sudah terpasang
- [ ] Model embedding BGE-M3 sudah di-download
- [ ] FAISS terinstall dan teruji
- [ ] Backend API bisa diakses di http://localhost:8000
- [ ] Celery worker berjalan dan berhubungan dengan Redis
- [ ] AI health check endpoint berhasil
- [ ] d.5.3 (AI Context Mapping) bisa dijalankan via API
- [ ] d.8.1 (NER) bisa dijalankan via API
- [ ] Nginx reverse proxy (opsional) terkonfigurasi

---

## 17. Ringkasan Timeline Instalasi

| Langkah | Estimasi Waktu |
|---|---|
| 1. Persiapan OS & hardware check | 30-60 menit |
| 2. Python environment setup | 30 menit |
| 3. Instalasi Ollama | 15 menit |
| 4. Unduh model AI | 30-120 menit (bisa lebih lama jika internet lambat) |
| 5. Instalasi FAISS & Redis | 15 menit |
| 6. Instalasi PostgreSQL | 20 menit |
| 7. Konfigurasi project & backend | 30 menit |
| 8. Konfigurasi service (systemd) | 20 menit |
| 9. Verifikasi instalasi | 30 menit |
| **Total** | **3-4 jam** (termasuk download model) |

> **Catatan:** Download model AI adalah langkah terberat. Qwen 2.5 7B (~4.5 GB) membutuhkan 30-60 menit tergantung kecepatan internet. Semua model hanya perlu di-download sati kali — setelah itu semua inference berjalan 100% offline.
