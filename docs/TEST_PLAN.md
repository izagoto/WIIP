# Test Plan — Evidentra Platform

## Versi Dokumen

| Properti | Nilai |
|---|---|
| **Versi** | 1.0 |
| **Tanggal** | 2026-08-05 |
| **Status** | Draft |

---

## 1. Strategi Testing

Testing dilakukan pada 4 level:

| Level | Tool | Cakupan | Target Coverage |
|---|---|---|---|
| Unit Test | pytest | Model, service, utils | ≥ 80% |
| Integration Test | pytest + httpx | API endpoints, database queries | ≥ 70% |
| E2E Test | Playwright | Alur kerja utama dari UI | ≥ 50% |
| Performance Test | Locust | API load testing | Semua endpoint critical |
| Security Test | OWASP ZAP + bandit | Kerentanan API dan kode | Semua endpoint |

---

## 2. Test Environment

| Komponen | Dev | Staging | Production |
|---|---|---|---|
| Database | SQLite | PostgreSQL | PostgreSQL |
| Cache | Redis (Docker) | Redis (Docker) | Redis (Cluster) |
| API | uvicorn (reload) | Gunicorn | Gunicorn + Nginx |
| Worker | Celery (solo) | Celery (prefork) | Celery (supervisor) |
| Frontend | Vite dev server | Nginx static | CDN + Nginx |

---

## 3. Test Cases per Fitur

### 3.1 d.5 — WhatsApp Intelligence

| ID | Fitur | Jenis Test | Deskripsi |
|---|---|---|---|
| TC-D5-001 | d.5.1 WhatsApp Data Acquisition | Unit | Validasi parsing msgstore.db menghasilkan data yang valid |
| TC-D5-002 | d.5.1 WhatsApp Data Acquisition | Unit | Validasi decrypt-wa.py menghasilkan key yang benar |
| TC-D5-003 | d.5.1 WhatsApp Data Acquisition | Integration | Validasi merge_dbs_sqlite menggabungkan multi-DB dengan benar |
| TC-D5-004 | d.5.2 Communication Profile Analyzer | Unit | Validasi hitung kontak dominan dan frekuensi interaksi |
| TC-D5-005 | d.5.2 Communication Profile Analyzer | Integration | Validasi analisis profil dari data WhatsApp yang sudah diekstrak |
| TC-D5-006 | d.5.3 AI Context Mapping | Unit | Validasi pipeline NLP/LLM menghasilkan topik dan entitas |
| TC-D5-007 | d.5.3 AI Context Mapping | Integration | Validasi konteks mapping dari percakapan WhatsApp |
| TC-D5-008 | d.5.4 Search, Filter & Insight Reporting | Unit | Validasi filter berdasarkan kontak, waktu, keyword |
| TC-D5-009 | d.5.4 Search, Filter & Insight Reporting | Integration | Validasi pencarian end-to-end dari API ke database |

### 3.2 d.6 — Tactical Operations & Case Platform

| ID | Fitur | Jenis Test | Deskripsi |
|---|---|---|---|
| TC-D6-001 | d.6.1 Case Registration | Unit | Validasi CRUD kasus |
| TC-D6-002 | d.6.1 Case Registration | Integration | Validasi pendaftaran kasus via API endpoint |
| TC-D6-003 | d.6.2 Investigation Dashboard | Integration | Validasi agregasi data kasus, prioritas, progres |
| TC-D6-004 | d.6.3 Task Assignment | Unit | Validasi penugasan tugas dengan checklist dan tenggat waktu |
| TC-D6-005 | d.6.3 Task Assignment | Integration | Validasi task assignment via API endpoint |
| TC-D6-006 | d.6.4 Kanban Workflow Tracking | Integration | Validasi perpindahan status TODO → IN_PROGRESS → DONE |
| TC-D6-007 | d.6.5 Organizational Hierarchy | Unit | Validasi struktur organisasi dan rantai koordinasi |
| TC-D6-008 | d.6.6 Identity & Access Management | Unit | Validasi registrasi pengguna dan RBAC |
| TC-D6-009 | d.6.6 Identity & Access Management | Integration | Validasi role-based endpoint protection |
| TC-D6-010 | d.6.7 System Audit & Logging | Integration | Validasi log audit tercatat untuk setiap aksi pengguna |
| TC-D6-011 | d.6.8 Report Generation Engine | Integration | Validasi PDF laporan dihasilkan dengan data yang benar |

### 3.3 d.7 — Digital Evidence Management

| ID | Fitur | Jenis Test | Deskripsi |
|---|---|---|---|
| TC-D7-001 | d.7.1 Central Evidence Repository | Unit | Validasi CRUD barang bukti |
| TC-D7-002 | d.7.1 Central Evidence Repository | Integration | Validasi pencarian dan arsip berdasarkan kasus dan kategori |
| TC-D7-003 | d.7.2 Evidence Registration Module | Unit | Validasi pencatatan metadata barang bukti |
| TC-D7-004 | d.7.2 Evidence Registration Module | Integration | Validasi registrasi via API endpoint |
| TC-D7-005 | d.7.3 Evidence Custody & Transfer Tracking | Integration | Validasi riwayat penguasaan dan perpindahan barang bukti |
| TC-D7-006 | d.7.4 Evidence Transfer Approval | Integration | Validasi workflow persetujuan dua pihak |
| TC-D7-007 | d.7.5 Evidence Integrity Verification | Unit | Validasi perhitungan hash SHA-256 |
| TC-D7-008 | d.7.5 Evidence Integrity Verification | Integration | Validasi deteksi perubahan data via re-hash |
| TC-D7-009 | d.7.6 Asset Vault Registry | Unit | Validasi pengelompokan berdasarkan lokasi dan kategori |
| TC-D7-010 | d.7.7 Custody Report Generator | Integration | Validasi BAST PDF dihasilkan dengan multi-barang bukti |
| TC-D7-011 | d.7.8 Geospatial Evidence Tracking | Integration | Validasi pencatatan dan visualisasi koordinat GPS/GIS |

### 3.4 d.8 — Strategic Intelligence & Correlation

| ID | Fitur | Jenis Test | Deskripsi |
|---|---|---|---|
| TC-D8-001 | d.8.1 Neural Document Correlation | Unit | Validasi NER pipeline mengekstrak entitas dari CSV/PDF |
| TC-D8-002 | d.8.1 Neural Document Correlation | Integration | Validasi NER extraction accuracy pada dataset sample |
| TC-D8-003 | d.8.2 Relationship Link Analysis | Unit | Validasi graph construction dari data komunikasi |
| TC-D8-004 | d.8.2 Relationship Link Analysis | Integration | Validasi graph analytics dan visualisasi data |
| TC-D8-005 | d.8.3 APK Static Analysis Inspector | Unit | Validasi parsing Android Manifest, izin, komponen |
| TC-D8-006 | d.8.3 APK Static Analysis Inspector | Integration | Validasi analysis APK statis via API endpoint |
| TC-D8-007 | d.8.4 Advanced Analysis Dashboard | Integration | Validasi metrik pemrosesan, status pekerjaan, hasil korelasi |

---

## 4. Performance Testing

### 4.1 Scenario

| Skenario | Deskripsi | Target |
|---|---|---|
| Concurrent Users | 50 pengguna simultan | Response time < 500ms |
| NER Batch Processing | 100 dokumen CSV/PDF | Processing time < 30s per dokumen |
| SHA-256 Hashing | 1000 file bukti | Hashing time < 5s per file |
| Dashboard Query | Real-time dashboard refresh | Response time < 2s |
| Database Query | Complex join query (evidence + case + custody) | Response time < 1s |

### 4.2 Locust Configuration

```python
from locust import HttpUser, task, between

class EvidentraUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def view_dashboard(self):
        self.client.get("/api/v1/cases/dashboard", headers={"Authorization": "Bearer <token>"})

    @task(2)
    def search_whatsapp(self):
        self.client.get("/api/v1/whatsapp/search?q=test", headers={"Authorization": "Bearer <token>"})

    @task(2)
    def list_cases(self):
        self.client.get("/api/v1/cases", headers={"Authorization": "Bearer <token>"})

    @task(1)
    def view_evidence(self):
        self.client.get("/api/v1/evidence", headers={"Authorization": "Bearer <token>"})
```

---

## 5. Security Testing

### 5.1 OWASP ZAP Scan

| Target | Endpoint |
|---|---|
| Authentication | `/api/v1/auth/login`, `/api/v1/auth/register` |
| Cases | `/api/v1/cases`, `/api/v1/cases/{id}` |
| Evidence | `/api/v1/evidence`, `/api/v1/evidence/{id}` |
| WhatsApp | `/api/v1/whatsapp/*` |
| Intelligence | `/api/v1/intelligence/*` |

### 5.2 Bandit Static Analysis

```bash
bandit -r backend/ -f html -o security-report.html
```

### 5.3 Test Checklist

- [ ] SQL Injection — semua endpoint menggunakan parameterized queries
- [ ] XSS — input validation pada semua request body
- [ ] CSRF — JWT token validation pada semua endpoint
- [ ] Authentication Bypass — RBAC middleware mencegah akses tanpa role yang benar
- [ ] Sensitive Data Exposure — password di-hash, token tidak terekspos di log
- [ ] Rate Limiting — API rate limit mencegah brute force

---

## 6. Test Data

| Entitas | Factory | Jumlah Sample |
|---|---|---|
| User (admin) | factory_boy | 2 |
| User (investigator) | factory_boy | 5 |
| User (viewer) | factory_boy | 3 |
| Cases | factory_boy | 20 |
| Tasks | factory_boy | 50 |
| Evidence | factory_boy | 30 |
| WhatsApp Conversations | factory_boy | 10 |
| WhatsApp Messages | factory_boy | 200 |
| Audit Logs | factory_boy | 100 |

---

## 7. Defect Management

| Severity | Keterangan | Target Fix |
|---|---|---|
| Critical | System crash, data loss, security vulnerability | Immediate |
| High | Feature broken, RBAC bypass, hash mismatch | Next sprint |
| Medium | Incorrect data display, performance issue | Next 2 sprints |
| Low | UI typo, minor cosmetic issue | Backlog |
