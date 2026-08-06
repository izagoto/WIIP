# Security Policy — Evidentra Platform

## Versi Dokumen

| Properti | Nilai |
|---|---|
| **Versi** | 1.0 |
| **Tanggal** | 2026-08-05 |
| **Status** | Draft |

---

## 1. Kebijakan Keamanan

### 1.1 Prinsip Keamanan

Evidentra mengikuti prinsip keamanan berikut dalam setiap tahap pengembangan:

1. **Defense in Depth** — Multiple layers of security controls
2. **Least Privilege** — Setiap pengguna dan komponen hanya memiliki akses minimum yang diperlukan
3. **Secure by Default** — Konfigurasi keamanan aktif secara default
4. **Fail Securely** — Kesalahan sistem tidak boleh membuka celah keamanan
5. **Audit Trail** — Semua aktivitas harus tercatat dan tidak dapat diubah

### 1.2 Data Classification

| Klasifikasi | Contoh Data | Penanganan |
|---|---|---|
| **Confidential** | Hasil analisis WhatsApp, data bukti digital, laporan BAST | Enkripsi at-rest, akses terbatas, audit log |
| **Internal** | Log audit, metadata kasus, struktur organisasi | Akses terbatas untuk anggota tim |
| **Public** | Dokumentasi teknis, API docs (tanpa sensitif) | Dapat diakses oleh stakeholder yang berwenang |

---

## 2. Autentikasi & Otorisasi

### 2.1 Autentikasi

- **JWT (JSON Web Token)** — Access token + Refresh token
- **Access Token** — Berlaku 30 menit
- **Refresh Token** — Berlaku 7 hari
- **Password Policy**:
  - Minimal 12 karakter
  - Harus mengandung huruf besar, huruf kecil, angka, dan karakter spesial
  - Tidak boleh mengandung username atau email
  - Password di-hash menggunakan bcrypt atau argon2-cffi

### 2.2 Otorisasi (RBAC)

| Role | Akses |
|---|---|
| **Admin** | Full access — semua modul, manajemen pengguna, pengaturan sistem |
| **Investigator** | Case management, task assignment, evidence management, WhatsApp analysis |
| **Viewer** | Read-only — lihat dashboard, laporan, dan data kasus |

### 2.3 Session Management

- JWT token disimpan di HTTP-only cookie (frontend) atau localStorage (alternatif)
- Token refresh dilakukan secara otomatis sebelum expiry
- Semua token yang sudah direvoke tidak dapat digunakan lagi

---

## 3. Perlindungan Data

### 3.1 Data at-Rest

| Data | Enkripsi |
|---|---|
| Database (PostgreSQL) | AES-256 (disk encryption) |
| File uploads (bukti digital) | AES-256 (server-side encryption) |
| Backup | AES-256 |
| WhatsApp backup keys | Terenkripsi di database |

### 3.2 Data in-Transit

- **HTTPS/TLS 1.3** — Semua komunikasi API menggunakan HTTPS
- **HSTS** — HTTP Strict Transport Security diaktifkan
- **CORS** — Dibatasi hanya untuk domain frontend yang terdaftar

### 3.3 Data Integrity

- **SHA-256 hashing** — Untuk setiap barang bukti digital yang terdaftar
- **Hash verification** — Otomatis dijalankan saat bukti diakses atau dipindah
- **Audit log** — Mencatat setiap perubahan hash atau metadata bukti

---

## 4. API Security

### 4.1 Input Validation

- Semua request body divalidasi menggunakan Pydantic v2
- SQL injection dicegah dengan SQLAlchemy ORM (parameterized queries)
- XSS dicegah dengan output encoding dan input sanitization

### 4.2 Rate Limiting

| Endpoint | Limit | Window |
|---|---|---|
| `/api/v1/auth/login` | 5 percobaan | 15 menit |
| `/api/v1/auth/register` | 3 percobaan | 1 jam |
| `/api/v1/*` (general) | 100 request | 1 menit |
| `/api/v1/intelligence/*` | 20 request | 1 menit |

### 4.3 Authentication Bypass Prevention

- Setiap endpoint dilindungi oleh RBAC middleware
- Role check dilakukan di level application, bukan hanya di level route
- Token revocation list untuk logout dan password change

---

## 5. Keamanan Infrastructure

### 5.1 Container Security

- Image dasar menggunakan versi resmi dan terbaru
- Tidak menjalankan container sebagai root
- Minimal image — hanya install dependensi yang diperlukan
- Regular vulnerability scanning pada Docker images

### 5.2 Database Security

- Database tidak terbuka ke public internet
- Connection menggunakan SSL/TLS
- Credential disimpan di environment variable (bukan di kode)
- Regular backup dengan enkripsi

### 5.3 Secret Management

- JWT secret, database password, dan credential lainnya disimpan di `.env` file
- `.env` file tidak boleh di-commit ke version control (sudah ada di `.gitignore`)
- Untuk produksi, gunakan secret manager (Vault, AWS Secrets Manager, dll.)

---

## 6. Vulnerability Reporting

Jika Anda menemukan kerentanan keamanan pada proyek ini, silakan laporkan melalui:

1. **Internal**: Hubungi tim keamanan proyek
2. **Email**: [security@evidentra.example.com] (ganti dengan email yang sesuai)
3. **Jangan** buka public issue untuk vulnerability yang belum difix

### Respons Timeline

| Severity | Target Response | Target Fix |
|---|---|---|
| Critical | 24 jam | 48 jam |
| High | 48 jam | 1 minggu |
| Medium | 1 minggu | 2 minggu |
| Low | 2 minggu | Next release |

---

## 7. Security Checklist untuk Setiap Sprint

- [ ] Semua endpoint dilindungi oleh RBAC middleware
- [ ] Input validation pada semua request body
- [ ] Tidak ada hardcoded secret di kode
- [ ] Log audit berjalan untuk semua operasi sensitif
- [ ] HTTPS enforced untuk semua komunikasi
- [ ] Rate limiting dikonfigurasi untuk semua endpoint
- [ ] OWASP ZAP scan dilakukan pada akhir sprint
- [ ] Bandit static analysis berjalan tanpa critical/high findings
- [ ] Database backup terenkripsi dan terjadwal
- [ ] Dependency audit (`pip audit`) dilakukan dan tidak ada vulnerability tinggi
