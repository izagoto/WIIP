# API Specification — Evidentra Platform

## Spesifikasi REST API

| Properti | Nilai |
|---|---|
| **Base URL** | `/api/v1` |
| **Format** | JSON |
| **Auth** | JWT Bearer Token |
| **Framework** | FastAPI |
| **Dokumentasi Otomatis** | `/api/docs` (Swagger UI) |

---

## Konvensi

### Enum dan Status

| Konteks | Format | Contoh |
|---|---|---|
| Database | lowercase snake_case | `todo`, `in_progress`, `open` |
| API — status kasus | lowercase snake_case | `open`, `in_progress`, `closed` |
| API — status Kanban task | UPPERCASE | `TODO`, `IN_PROGRESS`, `DONE` |

Mapping antara database dan API dilakukan di layer Pydantic schema.

### Identifikasi WhatsApp

| Field | Tipe | Keterangan |
|---|---|---|
| `conversation_id` (di API) | UUID | Primary key internal (`whatsapp_data.id`) |
| `wa_chat_jid` | string | Identifier asli WhatsApp (contoh: `62812...@s.whatsapp.net`) |

---

## Authentication

Akun **tidak** dapat didaftarkan sendiri melalui API publik. Akun admin pertama dibuat lewat `scripts/seed.py`; admin kemudian menambahkan investigator dan viewer melalui `POST /api/v1/users`.

### GET `/api/v1/auth/me`

Profil pengguna yang sedang login.

**Auth:** Bearer token (semua role)

**Response:** `200 OK`

```json
{
  "id": "uuid",
  "username": "string",
  "email": "string",
  "role": "string",
  "is_active": true,
  "created_at": "datetime"
}
```

### POST `/api/v1/auth/login`

Login dan dapatkan JWT token.

**Request Body:**

```json
{
  "email": "string",
  "password": "string"
}
```

**Response:** `200 OK`

```json
{
  "access_token": "string",
  "refresh_token": "string",
  "token_type": "bearer",
  "expires_in": "integer"
}
```

### POST `/api/v1/auth/refresh`

Perpanjang access token menggunakan refresh token.

**Request Body:**

```json
{
  "refresh_token": "string"
}
```

**Response:** `200 OK`

```json
{
  "access_token": "string",
  "token_type": "bearer",
  "expires_in": "integer"
}
```

### POST `/api/v1/auth/logout`

Revoke refresh token aktif (logout).

**Request Body:**

```json
{
  "refresh_token": "string"
}
```

**Response:** `204 No Content`

---

## d.5 — WhatsApp Intelligence

### POST `/api/v1/whatsapp/import`

Impor hasil ekstraksi WhatsApp (dari `extractors/whatsapp_extractor/`) ke database platform (d.5.1).

**Request Body:**

```json
{
  "case_id": "uuid",
  "device_id": "string",
  "account": "account_wa_1 | account_wa_2 | account_wa_business",
  "source_path": "string | null"
}
```

| Field | Keterangan |
|---|---|
| `case_id` | Kasus yang akan dikaitkan dengan data WhatsApp |
| `device_id` | ID perangkat (sesuai folder `data/raw_whatsapp_data/db/{device_id}/`) |
| `account` | Subfolder akun hasil decrypt |
| `source_path` | Opsional; override path absolut ke folder berisi `msgstore.db`. Default: path standar proyek |

**Response:** `202 Accepted`

```json
{
  "import_id": "uuid",
  "status": "queued | processing | completed | failed",
  "case_id": "uuid",
  "device_id": "string",
  "account": "string",
  "conversations_imported": "integer | null",
  "messages_imported": "integer | null"
}
```

Proses impor dijalankan sebagai background task (Celery). Gunakan `GET /api/v1/whatsapp/import/{import_id}` untuk memantau status.

### GET `/api/v1/whatsapp/import/{import_id}`

Status pekerjaan impor WhatsApp.

**Response:** `200 OK` — struktur sama dengan response `POST /api/v1/whatsapp/import`.

### GET `/api/v1/whatsapp/conversations`

Daftar percakapan WhatsApp yang sudah diekstrak.

**Query Parameters:**

| Parameter | Tipe | Deskripsi |
|---|---|---|
| `case_id` | `uuid` | Filter berdasarkan kasus |
| `contact` | `string` | Filter berdasarkan kontak |
| `start_date` | `date` | Filter tanggal mulai |
| `end_date` | `date` | Filter tanggal selesai |
| `keyword` | `string` | Pencarian berdasarkan kata kunci |
| `page` | `int` | Nomor halaman (default: 1) |
| `limit` | `int` | Jumlah per halaman (default: 50) |

**Response:** `200 OK`

```json
{
  "total": "integer",
  "page": "integer",
  "limit": "integer",
  "data": [
    {
      "id": "uuid",
      "case_id": "uuid",
      "contact": "string",
      "message_count": "integer",
      "first_message_date": "datetime",
      "last_message_date": "datetime",
      "group_name": "string | null"
    }
  ]
}
```

### GET `/api/v1/whatsapp/conversations/{conversation_id}/messages`

Daftar pesan dalam satu percakapan.

**Query Parameters:**

| Parameter | Tipe | Deskripsi |
|---|---|---|
| `keyword` | `string` | Filter berdasarkan kata kunci |
| `start_date` | `date` | Filter tanggal mulai |
| `end_date` | `date` | Filter tanggal selesai |
| `page` | `int` | Nomor halaman |
| `limit` | `int` | Jumlah per halaman |

**Response:** `200 OK`

```json
{
  "total": "integer",
  "page": "integer",
  "limit": "integer",
  "data": [
    {
      "id": "uuid",
      "conversation_id": "uuid",
      "timestamp": "datetime",
      "sender": "string",
      "receiver": "string",
      "content": "string",
      "content_type": "text | image | video | audio | document"
    }
  ]
}
```

### GET `/api/v1/whatsapp/profiles/{conversation_id}/summary`

Ringkasan profil komunikasi (d.5.2).

**Response:** `200 OK`

```json
{
  "conversation_id": "uuid",
  "dominant_contacts": [
    {
      "contact": "string",
      "message_count": "integer",
      "interaction_frequency": "float"
    }
  ],
  "active_groups": [
    {
      "group_name": "string",
      "message_count": "integer",
      "member_count": "integer"
    }
  ],
  "communication_patterns": {
    "peak_hours": ["integer"],
    "average_messages_per_day": "float",
    "most_active_day": "string"
  }
}
```

### POST `/api/v1/whatsapp/context-mapping`

Pemetaan konteks percakapan berbasis AI (d.5.3).

**Request Body:**

```json
{
  "conversation_id": "uuid",
  "topics_limit": "integer",
  "keywords": ["string"]
}
```

**Response:** `200 OK`

```json
{
  "conversation_id": "uuid",
  "topics": [
    {
      "topic": "string",
      "keywords": ["string"],
      "entities": ["string"],
      "related_discussions": ["uuid"]
    }
  ],
  "entities": [
    {
      "name": "string",
      "type": "person | location | organization | date",
      "mentions": "integer"
    }
  ]
}
```

### GET `/api/v1/whatsapp/search`

Pencarian dan filter (d.5.4).

**Query Parameters:**

| Parameter | Tipe | Wajib | Deskripsi |
|---|---|---|---|
| `q` | `string` | Ya | Kata kunci pencarian |
| `contact` | `string` | Tidak | Filter kontak |
| `start_date` | `date` | Tidak | Filter tanggal mulai |
| `end_date` | `date` | Tidak | Filter tanggal selesai |
| `content_type` | `string` | Tidak | Filter jenis konten |
| `page` | `int` | Tidak | Nomor halaman |
| `limit` | `int` | Tidak | Jumlah per halaman |

**Response:** `200 OK`

```json
{
  "total": "integer",
  "query": "string",
  "data": [
    {
      "id": "uuid",
      "conversation_id": "uuid",
      "timestamp": "datetime",
      "sender": "string",
      "content": "string",
      "snippet": "string"
    }
  ]
}
```

---

## d.6 — Tactical Operations & Case Platform

### POST `/api/v1/cases`

Registrasi kasus baru (d.6.1).

**Request Body:**

```json
{
  "title": "string",
  "description": "string",
  "priority": "low | medium | high | critical",
  "assigned_unit": "string",
  "assigned_investigator": "uuid",
  "metadata": "object"
}
```

**Response:** `201 Created`

```json
{
  "id": "uuid",
  "title": "string",
  "description": "string",
  "priority": "string",
  "status": "open",
  "assigned_unit": "string",
  "assigned_investigator": "uuid",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### GET `/api/v1/cases`

Daftar kasus.

**Query Parameters:**

| Parameter | Tipe | Deskripsi |
|---|---|---|
| `status` | `string` | Filter: open, in_progress, closed |
| `priority` | `string` | Filter: low, medium, high, critical |
| `assigned_to` | `uuid` | Filter berdasarkan personel |
| `page` | `int` | Nomor halaman |
| `limit` | `int` | Jumlah per halaman |

**Response:** `200 OK`

### GET `/api/v1/cases/{case_id}`

Detail kasus.

**Response:** `200 OK`

### PUT `/api/v1/cases/{case_id}`

Perbarui kasus.

### PATCH `/api/v1/cases/{case_id}/status`

Ubah status kasus.

**Request Body:**

```json
{
  "status": "open | in_progress | closed"
}
```

### GET `/api/v1/dashboard`

Dashboard investigasi global (d.6.2) — ringkasan seluruh kasus dan aktivitas sistem.

**Response:** `200 OK`

```json
{
  "total_cases": "integer",
  "by_priority": {
    "low": "integer",
    "medium": "integer",
    "high": "integer",
    "critical": "integer"
  },
  "by_status": {
    "open": "integer",
    "in_progress": "integer",
    "closed": "integer"
  },
  "task_load": {
    "total_tasks": "integer",
    "completed": "integer",
    "overdue": "integer"
  },
  "recent_activities": [
    {
      "id": "uuid",
      "action": "string",
      "user": "string",
      "timestamp": "datetime"
    }
  ]
}
```

### GET `/api/v1/cases/{case_id}/summary`

Ringkasan investigasi untuk satu kasus — tugas, bukti, dan aktivitas terkait kasus tersebut.

**Response:** `200 OK`

```json
{
  "case_id": "uuid",
  "title": "string",
  "status": "open | in_progress | closed",
  "priority": "low | medium | high | critical",
  "task_summary": {
    "total": "integer",
    "todo": "integer",
    "in_progress": "integer",
    "done": "integer",
    "overdue": "integer"
  },
  "evidence_count": "integer",
  "whatsapp_conversation_count": "integer",
  "recent_activities": [
    {
      "id": "uuid",
      "action": "string",
      "user": "string",
      "timestamp": "datetime"
    }
  ]
}
```

### GET `/api/v1/cases/{case_id}/tasks`

Daftar tugas dalam satu kasus.

### POST `/api/v1/cases/{case_id}/tasks`

Buat tugas baru (d.6.3).

**Request Body:**

```json
{
  "title": "string",
  "description": "string",
  "assignee": "uuid",
  "due_date": "datetime",
  "urgency": "low | medium | high",
  "checklist": ["string"]
}
```

### PATCH `/api/v1/tasks/{task_id}`

Perbarui tugas.

### GET `/api/v1/cases/{case_id}/kanban`

Papan kerja Kanban (d.6.4).

**Response:** `200 OK`

```json
{
  "columns": {
    "TODO": [
      {
        "id": "uuid",
        "title": "string",
        "assignee": "string",
        "due_date": "datetime",
        "urgency": "string"
      }
    ],
    "IN_PROGRESS": [...],
    "DONE": [...]
  }
}
```

### PATCH `/api/v1/tasks/{task_id}/move`

Pindahkan tugas antar kolom Kanban. Nilai `status` menggunakan format UPPERCASE; disimpan sebagai lowercase di database (`todo`, `in_progress`, `done`).

**Request Body:**

```json
{
  "status": "TODO | IN_PROGRESS | DONE"
}
```

### GET `/api/v1/organization/hierarchy`

Hierarki organisasi (d.6.5).

**Response:** `200 OK`

```json
{
  "id": "uuid",
  "name": "string",
  "role": "string",
  "parent_id": "uuid | null",
  "children": [...]
}
```

### GET `/api/v1/users`

Daftar pengguna (d.6.6). **Hanya admin.**

**Query Parameters:**

| Parameter | Tipe | Deskripsi |
|---|---|---|
| `role` | `string` | Filter role (`admin`, `investigator`, `viewer`) |
| `is_active` | `boolean` | Filter status aktif |
| `page` | `int` | Nomor halaman |
| `limit` | `int` | Jumlah per halaman |

**Response:** `200 OK`

```json
{
  "total": 0,
  "page": 1,
  "limit": 50,
  "data": [
    {
      "id": "uuid",
      "username": "string",
      "email": "string",
      "role": "string",
      "is_active": true,
      "created_at": "datetime"
    }
  ]
}
```

### GET `/api/v1/users/{user_id}`

Detail pengguna. **Hanya admin.**

**Response:** `200 OK` — sama seperti item di daftar pengguna.

### POST `/api/v1/users`

Buat akun investigator atau viewer baru. **Hanya admin.**

**Request Body:**

```json
{
  "username": "string",
  "email": "string",
  "password": "string",
  "role": "investigator | viewer"
}
```

**Response:** `201 Created`

```json
{
  "id": "uuid",
  "username": "string",
  "email": "string",
  "role": "string",
  "is_active": true,
  "created_at": "datetime"
}
```

### PATCH `/api/v1/users/{user_id}`

Perbarui pengguna. **Hanya admin.** Tidak menghapus data — gunakan `is_active` untuk menonaktifkan/mengaktifkan kembali.

**Request Body (semua field opsional):**

```json
{
  "email": "string",
  "role": "investigator | viewer",
  "is_active": true,
  "password": "string"
}
```

**Response:** `200 OK` — format sama seperti detail pengguna.

**Aturan:**
- Role `admin` tidak dapat diubah lewat API
- Admin tidak dapat menonaktifkan akun sendiri
- Admin terakhir yang masih aktif tidak dapat dinonaktifkan

### DELETE `/api/v1/users/{user_id}`

Nonaktifkan pengguna (soft delete). **Hanya admin.** Data tetap ada di database dengan `is_active: false`.

**Response:** `200 OK` — format sama seperti detail pengguna.

### PUT `/api/v1/users/{user_id}/role`

Ubah role pengguna.

### GET `/api/v1/audit-logs`

Log audit (d.6.7).

**Query Parameters:**

| Parameter | Tipe | Deskripsi |
|---|---|---|
| `user_id` | `uuid` | Filter berdasarkan pengguna |
| `action` | `string` | Filter berdasarkan aksi |
| `start_date` | `datetime` | Filter tanggal mulai |
| `end_date` | `datetime` | Filter tanggal selesai |
| `page` | `int` | Nomor halaman |
| `limit` | `int` | Jumlah per halaman |

**Response:** `200 OK`

### GET `/api/v1/cases/{case_id}/report`

Generate laporan PDF (d.6.8).

**Response:** `application/pdf`

---

## d.7 — Digital Evidence Management

### GET `/api/v1/evidence`

Daftar barang bukti (d.7.1).

**Query Parameters:**

| Parameter | Tipe | Deskripsi |
|---|---|---|
| `case_id` | `uuid` | Filter berdasarkan kasus |
| `category` | `string` | Filter kategori |
| `location` | `string` | Filter lokasi penyimpanan |
| `status` | `string` | Filter status |
| `page` | `int` | Nomor halaman |
| `limit` | `int` | Jumlah per halaman |

**Response:** `200 OK`

### POST `/api/v1/evidence`

Registrasi barang bukti baru (d.7.2).

**Request Body:**

```json
{
  "case_id": "uuid",
  "type": "device | mobile | document | media",
  "brand": "string",
  "imei": "string",
  "serial_number": "string",
  "capacity": "string",
  "condition_on_receipt": "string",
  "receipt_photo_url": "string",
  "location_latitude": "float",
  "location_longitude": "float",
  "storage_location": "string"
}
```

**Response:** `201 Created`

### GET `/api/v1/evidence/{evidence_id}/custody`

Riwayat custody barang bukti (d.7.3).

**Response:** `200 OK`

```json
{
  "evidence_id": "uuid",
  "custody_history": [
    {
      "id": "uuid",
      "holder": "string",
      "action": "received | transferred",
      "from": "string",
      "to": "string",
      "timestamp": "datetime",
      "notes": "string",
      "verified": "boolean"
    }
  ]
}
```

### POST `/api/v1/evidence/{evidence_id}/transfer`

Ajukan serah terima barang bukti (d.7.4).

**Request Body:**

```json
{
  "from_user_id": "uuid",
  "to_user_id": "uuid",
  "notes": "string"
}
```

### PATCH `/api/v1/evidence/transfers/{transfer_id}/approve`

Persetujuan serah terima (d.7.4).

**Request Body:**

```json
{
  "approved": "boolean",
  "notes": "string"
}
```

### GET `/api/v1/evidence/{evidence_id}/integrity`

Verifikasi integritas (d.7.5).

**Response:** `200 OK`

```json
{
  "evidence_id": "uuid",
  "sha256_hash": "string",
  "verified": "boolean",
  "last_verified_at": "datetime",
  "history": [
    {
      "hash": "string",
      "verified_at": "datetime",
      "verified_by": "uuid"
    }
  ]
}
```

### POST `/api/v1/evidence/{evidence_id}/verify-integrity`

Jalankan verifikasi integritas SHA-256 (d.7.5).

**Response:** `200 OK`

### GET `/api/v1/evidence/vault`

Registri vault aset (d.7.6).

**Query Parameters:**

| Parameter | Tipe | Deskripsi |
|---|---|---|
| `location` | `string` | Filter lokasi penyimpanan |
| `category` | `string` | Filter kategori |

### GET `/api/v1/evidence/{evidence_id}/custody-report`

Generate laporan BAST (d.7.7).

**Query Parameters:**

| Parameter | Tipe | Deskripsi |
|---|---|---|
| `evidence_ids` | `string[]` | Daftar ID barang bukti |

**Response:** `application/pdf`

### GET `/api/v1/evidence/geospatial`

Pelacakan spasial (d.7.8).

**Response:** `200 OK`

```json
{
  "locations": [
    {
      "evidence_id": "uuid",
      "latitude": "float",
      "longitude": "float",
      "acquired_at": "datetime",
      "case_id": "uuid"
    }
  ]
}
```

---

## d.8 — Strategic Intelligence & Correlation

### POST `/api/v1/intelligence/ner`

Neural Document Correlation (d.8.1).

**Request Body:**

```json
{
  "document_url": "string",
  "document_type": "csv | pdf",
  "entity_types": ["person | location | organization | date"]
}
```

**Response:** `200 OK`

```json
{
  "document_id": "uuid",
  "entities": [
    {
      "name": "string",
      "type": "person | location | organization | date",
      "confidence": "float",
      "context": "string"
    }
  ],
  "processed_at": "datetime"
}
```

### POST `/api/v1/intelligence/graph`

Relationship Link Analysis (d.8.2).

**Request Body:**

```json
{
  "source": "whatsapp | document",
  "source_id": "uuid",
  "entity_types": ["person | contact | location"]
}
```

**Response:** `200 OK`

```json
{
  "graph_id": "uuid",
  "nodes": [
    {
      "id": "string",
      "label": "string",
      "type": "person | contact | location",
      "properties": "object"
    }
  ],
  "edges": [
    {
      "source": "string",
      "target": "string",
      "weight": "float",
      "relationship": "string"
    }
  ]
}
```

### POST `/api/v1/intelligence/apk-analysis`

APK Static Analysis Inspector (d.8.3).

**Request Body:**

```json
{
  "apk_url": "string",
  "apk_filename": "string"
}
```

**Response:** `200 OK`

```json
{
  "analysis_id": "uuid",
  "package_name": "string",
  "version": "string",
  "permissions": ["string"],
  "components": {
    "activities": ["string"],
    "services": ["string"],
    "receivers": ["string"],
    "providers": ["string"]
  },
  "certificate": {
    "issuer": "string",
    "valid_from": "datetime",
    "valid_to": "datetime"
  },
  "threat_indicators": [
    {
      "type": "string",
      "description": "string",
      "severity": "low | medium | high | critical"
    }
  ]
}
```

### GET `/api/v1/intelligence/dashboard`

Advanced Analysis Dashboard (d.8.4).

**Response:** `200 OK`

```json
{
  "metrics": {
    "total_files_processed": "integer",
    "total_ner_extractions": "integer",
    "total_graph_analyses": "integer",
    "total_apk_analyses": "integer"
  },
  "job_status": {
    "queued": "integer",
    "running": "integer",
    "completed": "integer",
    "failed": "integer"
  },
  "correlation_results": [
    {
      "id": "uuid",
      "type": "ner | graph | apk",
      "status": "completed | failed",
      "created_at": "datetime"
    }
  ],
  "latency": {
    "average_ms": "integer",
    "p95_ms": "integer",
    "p99_ms": "integer"
  }
}
```

---

## Error Response

Semua endpoint error menggunakan format berikut:

```json
{
  "error": {
    "code": "string",
    "message": "string",
    "details": "object | null"
  }
}
```

### HTTP Status Codes

| Code | Keterangan |
|---|---|
| `400` | Bad Request — validasi gagal |
| `401` | Unauthorized — token tidak valid |
| `403` | Forbidden — tidak memiliki akses |
| `404` | Not Found — resource tidak ditemukan |
| `409` | Conflict — konflik data |
| `422` | Unprocessable Entity — data tidak valid |
| `500` | Internal Server Error |