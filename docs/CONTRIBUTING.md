# Panduan Kontribusi — Evidentra Platform

## Versi Dokumen

| Properti | Nilai |
|---|---|
| **Versi** | 1.0 |
| **Tanggal** | 2026-08-05 |
| **Status** | Draft |

---

## 1. Alur Kerja Kontribusi

### 1.1 Branch Strategy

| Branch | Keterangan |
|---|---|
| `main` | Produksi — tidak boleh langsung commit |
| `develop` | Development utama — integrasi fitur dari sprint |
| `feature/d5-xxx` | Fitur WhatsApp Intelligence |
| `feature/d6-xxx` | Fitur Tactical Operations |
| `feature/d7-xxx` | Fitur Digital Evidence Management |
| `feature/d8-xxx` | Fitur Strategic Intelligence |
| `hotfix/xxx` | Fix darurat untuk produksi |

### 1.2 Flow Kontribusi

```
1. Buat branch dari `develop`
2. Implementasi fitur/fix
3. Tulis unit test untuk fitur baru
4. Jalankan test suite — pastikan semua passing
5. Buat Pull Request ke `develop`
6. Minimal 1 reviewer approve
7. Merge ke `develop`
8. Sprint review — merge ke `main` di akhir sprint
```

---

## 2. Standar Kode

### 2.1 Python

- **Python version**: 3.11+
- **Linting**: `ruff` atau `flake8`
- **Formatting**: `black`
- **Type hints**: Wajib digunakan untuk semua fungsi dan parameter
- **Docstring**: Opsional; gunakan Google-style hanya untuk public API, service interface, dan modul kompleks
- **Komentar inline**: Hindari komentar yang hanya mengulang kode; kode harus self-explanatory melalui penamaan dan type hints
- **Import**: Urutan — standard library → third-party → local

### 2.2 TypeScript (Frontend)

- **Strict mode**: Wajib diaktifkan di `tsconfig.json`
- **Linting**: `eslint` + `prettier`
- **Formatting**: Prettier
- **Type safety**: Tidak boleh ada `any` kecuali dengan justifikasi

### 2.3 Naming Convention

| Elemen | Convention | Contoh |
|---|---|---|
| File | snake_case | `case_registration.py` |
| Class | PascalCase | `CaseRegistrationService` |
| Function | snake_case | `get_case_by_id()` |
| Constant | UPPER_SNAKE_CASE | `MAX_UPLOAD_SIZE` |
| Database table | snake_case plural | `whatsapp_conversations` |
| Database column | snake_case | `case_id`, `created_at` |
| API endpoint | kebab-case path | `/api/v1/cases` |
| Git branch | `feature/xxx` atau `fix/xxx` | `feature/d6-case-registration` |

---

## 3. Standar Commit

Menggunakan **Conventional Commits**:

| Prefix | Keterangan | Contoh |
|---|---|---|
| `feat:` | Fitur baru | `feat: add case registration API` |
| `fix:` | Bug fix | `fix: SHA-256 hash mismatch on large files` |
| `docs:` | Dokumentasi | `docs: update API specification` |
| `test:` | Test | `test: add unit tests for case CRUD` |
| `refactor:` | Refactoring | `refactor: extract WhatsApp parser into separate module` |
| `chore:` | Maintenance | `chore: update dependencies` |
| `perf:` | Performance | `perf: optimize NER inference pipeline` |
| `ci:` | CI/CD | `ci: add GitHub Actions workflow` |

---

## 4. Pull Request Template

```markdown
## Deskripsi

[Jelaskan perubahan yang dilakukan]

## Terkait

- Sprint: [Sprint X]
- Fitur: [d.X.X]
- Issue: [#XXX]

## Checklist

- [ ] Kode sudah mengikuti standar proyek
- [ ] Unit test sudah ditulis dan passing
- [ ] Integration test sudah ditulis (jika relevan)
- [ ] Dokumentasi sudah diperbarui
- [ ] Tidak ada breaking change
- [ ] Code review sudah dilakukan
```

---

## 5. Code Review Checklist

- [ ] Kode mengikuti standar penulisan proyek
- [ ] Type hints lengkap untuk semua fungsi
- [ ] Unit test tersedia dan passing
- [ ] Tidak ada hardcoded secret atau credential
- [ ] Error handling sudah dilakukan
- [ ] Log sudah ditambahkan untuk operasi penting
- [ ] Database migration tersedia (jika ada perubahan schema)
- [ ] API documentation sudah diperbarui
- [ ] Tidak ada breaking change (atau sudah dikomunikasikan)

---

## 6. Defect Reporting

Gunakan format berikut saat melaporkan defect:

```markdown
## Defect: [Judul]

**Sprint**: [Sprint X]
**Prioritas**: Critical / High / Medium / Low
**Modul**: [d.X.X]

### Reproduksi

1. [Langkah 1]
2. [Langkah 2]
3. [Langkah 3]

### Hasil yang Diharapkan

[Deskripsi hasil yang benar]

### Hasil yang Ditemukan

[Deskripsi hasil yang salah]

### Screenshot / Log

[Jika relevan]
```

---

## 7. Sprint Workflow

### 7.1 Awal Sprint

1. Sprint planning meeting — tentukan tugas untuk sprint ini
2. Setiap anggota mengambil tugas dari sprint backlog
3. Buat branch feature untuk setiap tugas

### 7.2 Selama Sprint

1. Commit secara rutin dengan pesan yang jelas
2. Push branch ke remote
3. Buat PR ketika tugas selesai
4. Code review oleh minimal 1 anggota tim lain

### 7.3 Akhir Sprint

1. Sprint review meeting — demo fitur yang sudah selesai
2. Sprint retrospective — evaluasi proses
3. Merge semua PR yang sudah approved ke `develop`
4. Jalankan full test suite
5. Deploy ke staging untuk verifikasi
6. Sprint review meeting dengan stakeholder
7. Merge `develop` ke `main` untuk release
