# Deployment Guide — Evidentra Platform

## Versi Dokumen

| Properti | Nilai |
|---|---|
| **Versi** | 1.0 |
| **Tanggal** | 2026-08-05 |
| **Status** | Draft |

---

## 1. Prasyarat Deploy

### 1.1 Server Requirements

| Komponen | Minimum | Recommended |
|---|---|---|
| OS | Ubuntu 22.04 LTS | Ubuntu 22.04 LTS |
| CPU | 4 cores | 8 cores |
| RAM | 8 GB | 16 GB |
| Storage | 100 GB SSD | 500 GB SSD |
| Python | 3.11+ | 3.11+ |
| PostgreSQL | 14+ | 15+ |
| Redis | 7+ | 7+ |
| Docker | 24+ | 24+ |
| Docker Compose | 2.0+ | 2.0+ |

### 1.2 Domain & SSL

- Domain harus diarahkan ke server
- SSL certificate (Let's Encrypt atau manual)
- Firewall: buka port 80 (HTTP), 443 (HTTPS), 22 (SSH)

---

## 2. Struktur Direktori Deploy

Struktur deploy mengikuti layout repository (`infra/docker/`):

```
/opt/evidentra/                          # clone repository
├── .env
├── infra/
│   ├── docker/
│   │   ├── docker-compose.yml
│   │   ├── Dockerfile.backend
│   │   ├── Dockerfile.worker
│   │   └── Dockerfile.frontend
│   └── nginx/
│       ├── nginx.conf
│       └── ssl/
├── backend/                             # FastAPI app (flat layout, tanpa src/)
│   └── alembic.ini                      # dibuat saat setup Alembic
├── worker/
├── data/
│   ├── postgres/
│   ├── uploads/
│   └── redis/
└── logs/
```

---

## 3. Konfigurasi Environment

### 3.1 `.env` File

```env
# Database
DATABASE_URL=postgresql://evidentra:password@postgres:5432/evidentra_db
DB_USER=evidentra
DB_PASSWORD=change-me-in-production
DB_HOST=postgres
DB_PORT=5432
DB_NAME=evidentra_db

# Redis
REDIS_URL=redis://redis:6379/0

# JWT
JWT_SECRET_KEY=change-me-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Environment
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# CORS
ALLOWED_ORIGINS=https://evidentra.example.com

# File Storage (development: filesystem, production: MinIO)
STORAGE_PATH=/opt/evidentra/data/uploads
MAX_UPLOAD_SIZE=100MB
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=change-me-in-production
MINIO_SECRET_KEY=change-me-in-production
MINIO_BUCKET=evidentra-evidence
MINIO_USE_SSL=false
```

---

## 4. Docker Compose Configuration

### 4.1 `infra/docker/docker-compose.yml`

Jalankan dari root repository:

```bash
docker compose -f infra/docker/docker-compose.yml up -d --build
```

```yaml
version: '3.8'

services:
  backend:
    build:
      context: ../..
      dockerfile: infra/docker/Dockerfile.backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://evidentra:password@postgres:5432/evidentra_db
      - REDIS_URL=redis://redis:6379/0
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - ENVIRONMENT=production
      - LOG_LEVEL=INFO
    volumes:
      - ../../data/uploads:/app/data/uploads
      - ../../logs:/app/logs
    depends_on:
      - postgres
      - redis
    restart: unless-stopped
    command: gunicorn backend.main:app --workers 4 --bind 0.0.0.0:8000 --worker-class uvicorn.workers.UvicornWorker

  worker:
    build:
      context: ../..
      dockerfile: infra/docker/Dockerfile.worker
    environment:
      - DATABASE_URL=postgresql://evidentra:password@postgres:5432/evidentra_db
      - REDIS_URL=redis://redis:6379/0
      - ENVIRONMENT=production
      - LOG_LEVEL=INFO
    volumes:
      - ../../data/uploads:/app/data/uploads
      - ../../logs:/app/logs
    depends_on:
      - postgres
      - redis
    restart: unless-stopped
    command: celery -A worker.celery_app worker --loglevel=info --concurrency=4

  postgres:
    image: postgres:15-alpine
    ports:
      - "5432:5432"
    environment:
      POSTGRES_USER: evidentra
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: evidentra_db
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

  minio:
    image: minio/minio:latest
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      MINIO_ROOT_USER: ${MINIO_ACCESS_KEY}
      MINIO_ROOT_PASSWORD: ${MINIO_SECRET_KEY}
    volumes:
      - minio_data:/data
    command: server /data --console-address ":9001"
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ../nginx/nginx.conf:/etc/nginx/nginx.conf
      - ../nginx/ssl:/etc/nginx/ssl
    depends_on:
      - backend
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  minio_data:
```

### 4.2 Nginx Configuration (`infra/nginx/nginx.conf`)

```nginx
upstream backend {
    server backend:8000;
}

server {
    listen 80;
    server_name evidentra.example.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name evidentra.example.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;

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
        proxy_set_header Host $host;
    }

    location /static/ {
        alias /app/static/;
        expires 30d;
    }
}
```

---

## 5. Langkah-langkah Deploy

### 5.1 Deploy Awal (First Time)

```bash
# 1. Clone repository
git clone <repository-url> /opt/evidentra
cd /opt/evidentra

# 2. Copy environment file
cp .env.example .env
# Edit .env dengan nilai yang sesuai

# 3. Buat direktori yang diperlukan
mkdir -p data/uploads logs

# 4. Build dan jalankan semua service
docker compose -f infra/docker/docker-compose.yml up -d --build

# 5. Jalankan database migration
docker compose -f infra/docker/docker-compose.yml exec backend alembic upgrade head

# 6. Buat admin user
docker compose -f infra/docker/docker-compose.yml exec backend python -m scripts.seed

# 7. Verifikasi semua service berjalan
docker compose -f infra/docker/docker-compose.yml ps
docker compose -f infra/docker/docker-compose.yml logs -f
```

### 5.2 Deploy Update

```bash
# 1. Pull kode terbaru
git pull origin main

# 2. Rebuild image
docker compose -f infra/docker/docker-compose.yml build

# 3. Jalankan migration
docker compose -f infra/docker/docker-compose.yml exec backend alembic upgrade head

# 4. Restart service
docker compose -f infra/docker/docker-compose.yml up -d --no-deps backend worker

# 5. Verifikasi
docker compose -f infra/docker/docker-compose.yml ps
docker compose -f infra/docker/docker-compose.yml logs backend
docker compose -f infra/docker/docker-compose.yml logs worker
```

### 5.3 Rollback

```bash
# 1. Kembali ke commit sebelumnya
git checkout <previous-commit>

# 2. Rebuild image
docker compose -f infra/docker/docker-compose.yml build

# 3. Restart service
docker compose -f infra/docker/docker-compose.yml up -d --no-deps backend worker

# 4. Verifikasi
docker compose -f infra/docker/docker-compose.yml ps
```

---

## 6. Monitoring & Maintenance

### 6.1 Log Monitoring

```bash
# Lihat log backend
docker compose -f infra/docker/docker-compose.yml logs -f backend

# Lihat log worker
docker compose -f infra/docker/docker-compose.yml logs -f worker

# Lihat log semua service
docker compose -f infra/docker/docker-compose.yml logs -f
```

### 6.2 Health Check

```bash
# Cek kesehatan API
curl -f https://evidentra.example.com/api/v1/dashboard || echo "API is down"

# Cek Redis
docker compose -f infra/docker/docker-compose.yml exec redis redis-cli ping

# Cek PostgreSQL
docker compose -f infra/docker/docker-compose.yml exec postgres psql -U evidentra -d evidentra_db -c "SELECT 1;"
```

### 6.3 Backup

```bash
# Backup PostgreSQL
docker compose -f infra/docker/docker-compose.yml exec postgres pg_dump -U evidentra evidentra_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Backup Redis
docker compose -f infra/docker/docker-compose.yml exec redis redis-cli BGSAVE

# Backup file uploads
tar -czf uploads_backup_$(date +%Y%m%d).tar.gz /opt/evidentra/data/uploads/
```

### 6.4 Update SSL Certificate

```bash
# Menggunakan Certbot (Let's Encrypt)
certbot certonly --nginx -d evidentra.example.com

# Restart nginx
docker compose -f infra/docker/docker-compose.yml restart nginx
```

---

## 7. Scaling

### 7.1 Horizontal Scaling API

```bash
# Tambah worker API
docker compose -f infra/docker/docker-compose.yml up -d --scale backend=3
```

### 7.2 Horizontal Scaling Workers

```bash
# Tambah Celery workers
docker compose -f infra/docker/docker-compose.yml up -d --scale worker=3
```

### 7.3 Database Connection Pooling

Tambahkan PgBouncer untuk connection pooling:

```yaml
# docker-compose.yml (infra/docker/)
pgbouncer:
  image: pgbouncer/pgbouncer
  ports:
    - "6432:6432"
  environment:
    DATABASE_URL: postgresql://evidentra:password@postgres:5432/evidentra_db
  depends_on:
    - postgres
```

---

## 8. Troubleshooting

| Masalah | Solusi |
|---|---|
| Backend tidak bisa connect ke PostgreSQL | Pastikan postgres service sudah running dan DATABASE_URL benar |
| Worker tidak memproses task | Pastikan Redis running dan REDIS_URL benar |
| API response lambat | Cek jumlah workers, database indexing, dan Redis caching |
| SSL certificate expired | Jalankan `certbot renew` dan restart nginx |
| Disk penuh | Hapus log lama, backup data, dan tambah storage |
| OOM (Out of Memory) | Tambah RAM atau kurangi jumlah workers |
