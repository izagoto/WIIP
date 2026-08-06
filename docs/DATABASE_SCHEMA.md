# Database Schema Documentation — Evidentra Platform

## Versi Dokumen

| Properti | Nilai |
|---|---|
| **Versi** | 1.0 |
| **Tanggal** | 2026-08-05 |
| **Status** | Draft |

---

## 1. Database Overview

Evidentra menggunakan **PostgreSQL** sebagai database produksi dan **SQLite** untuk development/testing.

### 1.1 Connection

| Environment | URL |
|---|---|
| Development | `sqlite:///./evidentra.db` |
| Production | `postgresql://evidentra:<password>@postgres:5432/evidentra_db` |

### 1.2 ORM

Menggunakan **SQLAlchemy 2.0** dengan **Alembic** untuk migrasi database.

### 1.3 Konvensi Enum

| Konteks | Format | Contoh |
|---|---|---|
| Kolom database | lowercase snake_case | `todo`, `in_progress`, `open` |
| API — status kasus | lowercase snake_case | `open`, `in_progress`, `closed` |
| API — status Kanban task | UPPERCASE (di layer Pydantic) | `TODO`, `IN_PROGRESS`, `DONE` |

### 1.4 Object Storage (MinIO)

File bukti digital, dokumen NER, dan APK disimpan di **MinIO** (produksi) atau filesystem lokal (development). Metadata file dicatat di tabel `documents`; kolom `file_url` berisi path/URL object storage.

| Environment | Storage |
|---|---|
| Development | `STORAGE_PATH` lokal (filesystem) |
| Production | MinIO bucket (`MINIO_BUCKET`, `MINIO_ENDPOINT`) |

---

## 2. Entity Relationship Diagram

```
┌─────────────┐       ┌─────────────────┐       ┌─────────────────┐
│   users      │       │    cases        │       │   tasks         │
├─────────────┤       ├─────────────────┤       ├─────────────────┤
│ id (PK)      │──┐    │ id (PK)         │──┐    │ id (PK)         │
│ username      │  │    │ title           │  │    │ case_id (FK)    │
│ email         │  │    │ description     │  │    │ title           │
│ password_hash │  │    │ priority        │  │    │ description     │
│ role          │  │    │ status          │  │    │ assignee_id(FK) │
│ created_at    │  └───▶│ assigned_unit   │  └───▶│ due_date        │
│ updated_at    │       │ assigned_to(FK) │       │ urgency         │
└─────────────┘       │ created_at      │       │ checklist       │
                       │ updated_at      │       │ status          │
                       └─────────────────┘       │ created_at      │
                                                  │ updated_at      │
                                                  └─────────────────┘

┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│  whatsapp_data   │       │   evidence      │       │  custody_logs   │
├─────────────────┤       ├─────────────────┤       ├─────────────────┤
│ id (PK)          │       │ id (PK)         │       │ id (PK)          │
│ case_id (FK)     │       │ case_id (FK)    │       │ evidence_id(FK)  │
│ wa_chat_jid      │       │ type            │       │ holder_id(FK)    │
│ contact          │       │ brand           │       │ action           │
│ message_count    │       │ imei            │       │ from_user_id(FK) │
│ first_msg_date   │       │ serial_number   │       │ to_user_id(FK)   │
│ last_msg_date    │       │ capacity        │       │ timestamp        │
│ group_name       │       │ condition       │       │ notes            │
│ created_at       │       │ receipt_photo   │       │ verified         │
└─────────────────┘       │ location_lat    │       │ created_at       │
                          │ location_lng    │       └─────────────────┘
                          │ storage_location│
                          │ sha256_hash     │       ┌─────────────────┐
                          │ created_at      │       │  audit_logs     │
                          │ updated_at      │       ├─────────────────┤
                          └─────────────────┘       │ id (PK)          │
                                                    │ user_id (FK)     │
                                                    │ action           │
                                                    │ entity_type      │
                                                    │ entity_id        │
                                                    │ details          │
                                                    │ timestamp        │
                                                    └─────────────────┘

┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│  transfer_approvals│     │  ner_entities   │       │  graph_nodes    │
├─────────────────┤       ├─────────────────┤       ├─────────────────┤
│ id (PK)          │       │ id (PK)         │       │ id (PK)          │
│ evidence_id(FK)  │       │ document_id(FK) │       │ graph_id(FK)     │
│ from_user_id(FK) │       │ name            │       │ node_id          │
│ to_user_id(FK)   │       │ entity_type     │       │ label            │
│ status           │       │ confidence      │       │ node_type        │
│ approved_by(FK)  │       │ context         │       │ properties       │
│ approved_at      │       │ created_at      │       │ created_at       │
│ created_at       │       └─────────────────┘       └─────────────────┘
└─────────────────┘

┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│  graph_edges     │       │  apk_analysis   │       │  org_hierarchy  │
├─────────────────┤       ├─────────────────┤       ├─────────────────┤
│ id (PK)          │       │ id (PK)         │       │ id (PK)          │
│ graph_id (FK)    │       │ analysis_id(FK) │       │ user_id (FK)     │
│ source_node_id   │       │ package_name    │       │ parent_id (FK)   │
│ target_node_id   │       │ version         │       │ name             │
│ weight           │       │ permissions     │       │ role             │
│ relationship     │       │ components      │       │ created_at       │
│ created_at       │       │ certificate     │       │ created_at       │
└─────────────────┘       │ threat_indicators│      └─────────────────┘
                          │ created_at       │
                          └─────────────────┘

┌─────────────────┐       ┌─────────────────┐
│  documents       │       │  dashboard_metrics│
├─────────────────┤       ├─────────────────┤
│ id (PK)          │       │ id (PK)          │
│ case_id (FK)     │       │ metric_key       │
│ file_name        │       │ metric_value     │
│ file_type        │       │ timestamp        │
│ file_url         │       └─────────────────┘
│ extracted_text   │
│ created_at       │
└─────────────────┘
```

---

## 3. Table Definitions

### 3.1 `users`

| Kolom | Tipe | Constraint | Keterangan |
|---|---|---|---|
| `id` | UUID | PK, default gen_random_uuid() | ID unik pengguna |
| `username` | VARCHAR(50) | NOT NULL, UNIQUE | Nama pengguna |
| `email` | VARCHAR(255) | NOT NULL, UNIQUE | Email pengguna |
| `password_hash` | VARCHAR(255) | NOT NULL | Password di-hash dengan bcrypt |
| `role` | VARCHAR(20) | NOT NULL, CHECK | admin, investigator, viewer |
| `is_active` | BOOLEAN | default true | Status aktif |
| `created_at` | TIMESTAMP | default NOW() | Waktu pembuatan |
| `updated_at` | TIMESTAMP | default NOW() | Waktu pembaruan |

### 3.2 `cases`

| Kolom | Tipe | Constraint | Keterangan |
|---|---|---|---|
| `id` | UUID | PK | ID unik kasus |
| `title` | VARCHAR(255) | NOT NULL | Judul kasus |
| `description` | TEXT | | Deskripsi kasus |
| `priority` | VARCHAR(10) | NOT NULL, CHECK | low, medium, high, critical |
| `status` | VARCHAR(20) | NOT NULL, default 'open' | open, in_progress, closed |
| `assigned_unit` | VARCHAR(100) | | Unit penanggung jawab |
| `assigned_to` | UUID | FK → users(id) | Investigator yang ditugaskan |
| `created_by` | UUID | FK → users(id) | Pembuat kasus |
| `created_at` | TIMESTAMP | default NOW() | Waktu pembuatan |
| `updated_at` | TIMESTAMP | default NOW() | Waktu pembaruan |

### 3.3 `tasks`

| Kolom | Tipe | Constraint | Keterangan |
|---|---|---|---|
| `id` | UUID | PK | ID unik tugas |
| `case_id` | UUID | FK → cases(id), NOT NULL | Kasus terkait |
| `title` | VARCHAR(255) | NOT NULL | Judul tugas |
| `description` | TEXT | | Deskripsi tugas |
| `assignee_id` | UUID | FK → users(id) | Personel yang ditugaskan |
| `due_date` | TIMESTAMP | | Tenggat waktu |
| `urgency` | VARCHAR(10) | CHECK | low, medium, high |
| `checklist` | JSONB | | Daftar checklist |
| `status` | VARCHAR(20) | default 'todo' | todo, in_progress, done |
| `created_at` | TIMESTAMP | default NOW() | |
| `updated_at` | TIMESTAMP | default NOW() | |

### 3.4 `whatsapp_data`

Ringkasan percakapan WhatsApp per kasus. `wa_chat_jid` adalah identifier asli dari WhatsApp; `id` (UUID) digunakan sebagai `conversation_id` di API.

| Kolom | Tipe | Constraint | Keterangan |
|---|---|---|---|
| `id` | UUID | PK | ID internal — dipakai sebagai `conversation_id` di API |
| `case_id` | UUID | FK → cases(id) | Kasus terkait |
| `wa_chat_jid` | VARCHAR(255) | NOT NULL | JID percakapan WhatsApp asli (contoh: `62812...@s.whatsapp.net`) |
| `contact` | VARCHAR(255) | | Nama kontak |
| `message_count` | INTEGER | default 0 | Jumlah pesan |
| `first_message_date` | TIMESTAMP | | Tanggal pesan pertama |
| `last_message_date` | TIMESTAMP | | Tanggal pesan terakhir |
| `group_name` | VARCHAR(255) | | Nama grup (jika grup) |
| `created_at` | TIMESTAMP | default NOW() | |

**Unique constraint:** `(case_id, wa_chat_jid)` — satu JID per kasus.

### 3.5 `whatsapp_messages`

| Kolom | Tipe | Constraint | Keterangan |
|---|---|---|---|
| `id` | UUID | PK | ID unik pesan |
| `conversation_record_id` | UUID | FK → whatsapp_data(id), NOT NULL | Referensi ke baris `whatsapp_data` |
| `timestamp` | TIMESTAMP | NOT NULL | Waktu pesan |
| `sender` | VARCHAR(255) | NOT NULL | Pengirim |
| `receiver` | VARCHAR(255) | NOT NULL | Penerima |
| `content` | TEXT | NOT NULL | Isi pesan |
| `content_type` | VARCHAR(20) | default 'text' | text, image, video, audio, document |
| `created_at` | TIMESTAMP | default NOW() | |

### 3.6 `evidence`

| Kolom | Tipe | Constraint | Keterangan |
|---|---|---|---|
| `id` | UUID | PK | ID unik bukti |
| `case_id` | UUID | FK → cases(id) | Kasus terkait |
| `type` | VARCHAR(20) | NOT NULL | device, mobile, document, media |
| `brand` | VARCHAR(100) | | Merek |
| `imei` | VARCHAR(25) | | Nomor IMEI |
| `serial_number` | VARCHAR(100) | | Nomor seri |
| `capacity` | VARCHAR(50) | | Kapasitas penyimpanan |
| `condition_on_receipt` | TEXT | | Kondisi saat diterima |
| `receipt_photo_url` | VARCHAR(500) | | URL foto penerimaan |
| `location_latitude` | DECIMAL(10, 8) | | Latitude lokasi perolehan |
| `location_longitude` | DECIMAL(11, 8) | | Longitude lokasi perolehan |
| `storage_location` | VARCHAR(255) | | Lokasi penyimpanan |
| `sha256_hash` | VARCHAR(64) | | Hash SHA-256 untuk integritas |
| `created_at` | TIMESTAMP | default NOW() | |
| `updated_at` | TIMESTAMP | default NOW() | |

### 3.7 `custody_logs`

| Kolom | Tipe | Constraint | Keterangan |
|---|---|---|---|
| `id` | UUID | PK | ID unik |
| `evidence_id` | UUID | FK → evidence(id) | Barang bukti terkait |
| `holder_id` | UUID | FK → users(id) | Pemegang aktif |
| `action` | VARCHAR(20) | NOT NULL | received, transferred |
| `from_user_id` | UUID | FK → users(id) | Pengirim |
| `to_user_id` | UUID | FK → users(id) | Penerima |
| `timestamp` | TIMESTAMP | NOT NULL | Waktu serah terima |
| `notes` | TEXT | | Catatan |
| `verified` | BOOLEAN | default false | Status verifikasi |
| `created_at` | TIMESTAMP | default NOW() | |

### 3.8 `transfer_approvals`

| Kolom | Tipe | Constraint | Keterangan |
|---|---|---|---|
| `id` | UUID | PK | ID unik |
| `evidence_id` | UUID | FK → evidence(id) | Barang bukti terkait |
| `from_user_id` | UUID | FK → users(id) | Pengirim |
| `to_user_id` | UUID | FK → users(id) | Penerima |
| `status` | VARCHAR(20) | default 'pending' | pending, approved, rejected |
| `approved_by` | UUID | FK → users(id) | Approver |
| `approved_at` | TIMESTAMP | | Waktu persetujuan |
| `notes` | TEXT | | Catatan |
| `created_at` | TIMESTAMP | default NOW() | |

### 3.9 `audit_logs`

| Kolom | Tipe | Constraint | Keterangan |
|---|---|---|---|
| `id` | UUID | PK | ID unik |
| `user_id` | UUID | FK → users(id) | Pengguna yang melakukan aksi |
| `action` | VARCHAR(50) | NOT NULL | Jenis aksi |
| `entity_type` | VARCHAR(50) | | Tipe entitas (case, evidence, user, dll.) |
| `entity_id` | UUID | | ID entitas yang diubah |
| `details` | JSONB | | Detail perubahan |
| `ip_address` | VARCHAR(45) | | Alamat IP |
| `timestamp` | TIMESTAMP | default NOW() | |

### 3.10 `documents`

| Kolom | Tipe | Constraint | Keterangan |
|---|---|---|---|
| `id` | UUID | PK | ID unik |
| `case_id` | UUID | FK → cases(id) | Kasus terkait |
| `file_name` | VARCHAR(255) | NOT NULL | Nama file |
| `file_type` | VARCHAR(20) | NOT NULL | csv, pdf, apk, dll. |
| `file_url` | VARCHAR(500) | NOT NULL | URL/path object di MinIO atau filesystem lokal |
| `extracted_text` | TEXT | | Teks yang diekstrak |
| `created_at` | TIMESTAMP | default NOW() | |

### 3.11 `ner_entities`

| Kolom | Tipe | Constraint | Keterangan |
|---|---|---|---|
| `id` | UUID | PK | ID unik |
| `document_id` | UUID | FK → documents(id) | Dokumen terkait |
| `name` | VARCHAR(255) | NOT NULL | Nama entitas |
| `entity_type` | VARCHAR(20) | NOT NULL | person, location, organization, date |
| `confidence` | DECIMAL(3, 2) | | Confidence score (0.00–1.00) |
| `context` | TEXT | | Konteks kemunculan |
| `created_at` | TIMESTAMP | default NOW() | |

### 3.12 `graph_nodes`

| Kolom | Tipe | Constraint | Keterangan |
|---|---|---|---|
| `id` | UUID | PK | ID unik |
| `graph_id` | UUID | NOT NULL | ID graf |
| `node_id` | VARCHAR(255) | NOT NULL | ID node |
| `label` | VARCHAR(255) | NOT NULL | Label node |
| `node_type` | VARCHAR(20) | NOT NULL | person, contact, location |
| `properties` | JSONB | | Properti tambahan |
| `created_at` | TIMESTAMP | default NOW() | |

### 3.13 `graph_edges`

| Kolom | Tipe | Constraint | Keterangan |
|---|---|---|---|
| `id` | UUID | PK | ID unik |
| `graph_id` | UUID | NOT NULL | ID graf |
| `source_node_id` | VARCHAR(255) | NOT NULL | Node sumber |
| `target_node_id` | VARCHAR(255) | NOT NULL | Node target |
| `weight` | DECIMAL(5, 2) | default 1.0 | Bobot hubungan |
| `relationship` | VARCHAR(50) | | Jenis hubungan |
| `created_at` | TIMESTAMP | default NOW() | |

### 3.14 `apk_analysis`

| Kolom | Tipe | Constraint | Keterangan |
|---|---|---|---|
| `id` | UUID | PK | ID unik |
| `document_id` | UUID | FK → documents(id) | Dokumen APK terkait |
| `package_name` | VARCHAR(255) | | Nama paket |
| `version` | VARCHAR(50) | | Versi APK |
| `permissions` | JSONB | | Daftar izin |
| `components` | JSONB | | Activities, services, receivers, providers |
| `certificate` | JSONB | | Info sertifikat |
| `threat_indicators` | JSONB | | Indikator ancaman |
| `created_at` | TIMESTAMP | default NOW() | |

### 3.15 `org_hierarchy`

| Kolom | Tipe | Constraint | Keterangan |
|---|---|---|---|
| `id` | UUID | PK | ID unik |
| `user_id` | UUID | FK → users(id) | Pengguna terkait |
| `parent_id` | UUID | FK → org_hierarchy(id) | Atasan langsung |
| `name` | VARCHAR(255) | NOT NULL | Nama unit/divisi |
| `role` | VARCHAR(50) | | Peran dalam hierarki |
| `created_at` | TIMESTAMP | default NOW() | |

### 3.16 `dashboard_metrics`

| Kolom | Tipe | Constraint | Keterangan |
|---|---|---|---|
| `id` | UUID | PK | ID unik |
| `metric_key` | VARCHAR(100) | NOT NULL | Kunci metrik |
| `metric_value` | JSONB | NOT NULL | Nilai metrik |
| `timestamp` | TIMESTAMP | default NOW() | |

### 3.17 `whatsapp_imports`

Pelacakan pekerjaan impor WhatsApp (`POST /api/v1/whatsapp/import`).

| Kolom | Tipe | Constraint | Keterangan |
|---|---|---|---|
| `id` | UUID | PK | ID impor (`import_id` di API) |
| `case_id` | UUID | FK → cases(id), NOT NULL | Kasus target |
| `device_id` | VARCHAR(100) | NOT NULL | ID perangkat sumber |
| `account` | VARCHAR(50) | NOT NULL | Nama folder akun (`account_wa_1`, dll.) |
| `source_path` | VARCHAR(500) | | Path override ke folder `msgstore.db` |
| `status` | VARCHAR(20) | default 'queued' | queued, processing, completed, failed |
| `conversations_imported` | INTEGER | | Jumlah percakapan yang diimpor |
| `messages_imported` | INTEGER | | Jumlah pesan yang diimpor |
| `error_message` | TEXT | | Pesan error jika gagal |
| `celery_task_id` | VARCHAR(255) | | ID task Celery terkait |
| `created_at` | TIMESTAMP | default NOW() | |
| `completed_at` | TIMESTAMP | | Waktu selesai |

---

## 4. Indexes

| Tabel | Kolom | Jenis Index | Alasan |
|---|---|---|---|
| `cases` | `status` | B-tree | Filter status kasus |
| `cases` | `priority` | B-tree | Filter prioritas |
| `cases` | `assigned_to` | B-tree | Cari kasus per personel |
| `tasks` | `case_id` | B-tree | Join kasus-tugas |
| `tasks` | `status` | B-tree | Filter status tugas |
| `tasks` | `assignee_id` | B-tree | Cari tugas per personel |
| `whatsapp_data` | `case_id` | B-tree | Join kasus-WhatsApp |
| `whatsapp_data` | `wa_chat_jid` | B-tree | Pencarian berdasarkan JID WhatsApp |
| `whatsapp_data` | `contact` | B-tree | Pencarian berdasarkan kontak |
| `whatsapp_data` | `(case_id, wa_chat_jid)` | UNIQUE | Satu JID per kasus |
| `whatsapp_messages` | `conversation_record_id` | B-tree | Join percakapan-pesan |
| `evidence` | `case_id` | B-tree | Join kasus-bukti |
| `evidence` | `sha256_hash` | B-tree | Pencarian berdasarkan hash |
| `custody_logs` | `evidence_id` | B-tree | Join bukti-riwayat custody |
| `audit_logs` | `user_id` | B-tree | Filter log per pengguna |
| `audit_logs` | `timestamp` | B-tree | Filter log berdasarkan waktu |
| `ner_entities` | `document_id` | B-tree | Join dokumen-entitas |
| `graph_nodes` | `graph_id` | B-tree | Join graf-node |
| `graph_edges` | `graph_id` | B-tree | Join graf-edge |

---

## 5. Alembic Migration

### 5.1 Setup

```bash
# Inisialisasi Alembic
alembic init alembic

# Konfigurasi alembic.ini
# Set sqlalchemy.url ke DATABASE_URL
```

### 5.2 Membuat Migration

```bash
# Buat migration baru
alembic revision --autogenerate -m "create initial tables"

# Jalankan migration
alembic upgrade head
```

### 5.3 Migration History

| Revision | Deskripsi | Tanggal |
|---|---|---|
| `base` | Buat semua tabel awal | 2026-08-05 |

### 5.4 Diagram Visual (dbdiagram.io)

File DBML untuk import ke [dbdiagram.io](https://dbdiagram.io/d):

```
docs/evidentra.dbml
```

Cara pakai:
1. Buka https://dbdiagram.io/d
2. Hapus konten default di panel kiri
3. Copy-paste seluruh isi `docs/evidentra.dbml`
4. Diagram ERD akan ter-render otomatis dengan relasi dan table groups per modul

---

## 6. Database Seeding

Untuk keperluan development dan testing, data sample dapat di-seed menggunakan factory_boy:

```python
# scripts/seed_data.py
import factory
from sqlalchemy.orm import Session
from models import User, Case, Evidence, Task

class UserFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = User
        sqlalchemy_session = Session

    username = factory.Sequence(lambda n: f"user_{n}")
    email = factory.Sequence(lambda n: f"user_{n}@example.com")
    role = "investigator"
    is_active = True

class CaseFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Case
        sqlalchemy_session = Session

    title = factory.Faker("sentence")
    priority = "medium"
    status = "open"
```
