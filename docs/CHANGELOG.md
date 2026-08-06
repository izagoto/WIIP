# CHANGELOG — Evidentra Platform

Semua perubahan signifikan pada proyek ini akan didokumentasikan di file ini.

Format berdasarkan [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) dan menggunakan [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added

- Dokumentasi skenario proyek (`docs/PROJECT_SCENARIO.md`)
- Dokumentasi kebutuhan peran tim (`docs/ROLE_REQUIREMENTS.md`)
- Spesifikasi API (`docs/API_SPECIFICATION.md`)
- Desain arsitektur (`docs/ARCHITECTURE.md`)
- Rencana test (`docs/TEST_PLAN.md`)
- Panduan deployment (`docs/DEPLOYMENT.md`)
- Panduan kontribusi (`docs/CONTRIBUTING.md`)

---

## [0.1.0] — 2026-08-05

### Added

- Kode awal WhatsApp extractor (`extractors/whatsapp_extractor/`)
  - `decrypt-wa.py` — dekripsi backup WhatsApp
  - `extract_keys_wa.py` — ekstraksi kunci enkripsi
  - `merge_dbs_sqlite.py` — penggabungan database SQLite
  - `whatsapp_backup_setup.py` — setup otomatis backup WhatsApp
  - `cmd.py` — antarmuka command-line
  - `get_number_wa.py` — ekstraksi nomor WhatsApp
  - Proto buffers untuk WhatsApp crypto (`proto/`)
- Struktur direktori proyek (`data/`, `extractors/`, `docs/`)
- `requirements.txt` dengan dependensi awal
- `pyrightconfig.json` untuk type checking
- `.gitignore` untuk file yang tidak perlu di-commit
- `README.md` (awalnya kosong)

### Known Issues

- WhatsApp extractor belum terintegrasi dengan API backend
- Belum ada modul d.6–d.8
- Belum ada frontend dashboard
- Belum ada test suite
- `README.md` masih kosong
