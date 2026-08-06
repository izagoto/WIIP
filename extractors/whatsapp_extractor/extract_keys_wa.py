import os
import uiautomator2 as u2
import sys
import subprocess
import logging

from paths import (
    account_db_dir,
    account_key_dir,
    cleanup_pull_account_dir,
    decrypted_db_file,
    decrypted_wa_db_file,
    ensure_account_dirs,
    key_file,
    pull_account_dir,
    pulled_db_file,
    pulled_wa_db_file,
)

logger = logging.getLogger(__name__)

class WhatsappTools:
    def __init__(self, package_name="com.whatsapp", account_suffix="_account1"):
        self.package_name = package_name
        self.account_suffix = account_suffix
        try:
            logger.info(f"[INFO] Menghubungkan ke perangkat untuk paket {self.package_name} (Akun: {self.account_suffix})...")
            self.d = u2.connect()
            if not self.d.info:
                raise ConnectionError("[ERROR] Tidak dapat terhubung ke perangkat.")
            
            self.device_id = self.get_device_id()
            ensure_account_dirs(self.device_id, self.account_suffix)

            self.pull_path = pull_account_dir(self.device_id, self.account_suffix)
            self.key_dir = account_key_dir(self.device_id, self.account_suffix)
            self.db_path = account_db_dir(self.device_id, self.account_suffix)

            self.output_file = key_file(self.device_id, self.account_suffix)
            self.backup_db = decrypted_db_file(self.device_id, self.account_suffix)
            self.database_file = pulled_db_file(self.device_id, self.account_suffix)
            self.wa_database_file = pulled_wa_db_file(self.device_id, self.account_suffix)
        except Exception as e:
            logger.info(f"[ERROR] Gagal menghubungkan ke perangkat: {e}")
            sys.exit(1)

    def get_device_id(self):
        try:
            result = subprocess.run(["adb", "devices"], capture_output=True, text=True, check=True)
            devices = result.stdout.strip().split("\n")[1:]
            
            if not devices or devices[0] == "":
                logger.warning("[ERROR] Tidak ada perangkat ADB yang terhubung.")
                sys.exit(1)
            
            device_id = devices[0].split("\t")[0]
            return device_id
        except Exception as e:
            logger.error(f"[ERROR] Gagal mendapatkan device ID: {e}")
            sys.exit(1)

    def extract_whatsapp_keys(self):
        try:
            logger.info("[INFO] Mencari elemen EditText di WhatsApp...")
            edit_text_fields = self.d(className="android.widget.EditText")

            if edit_text_fields.exists:
                keys = [field.get_text().strip() for field in edit_text_fields if field.get_text()]
                extracted_key = "".join(keys)

                if extracted_key:
                    logger.info(f"[SUCCESS] Kunci enkripsi ditemukan: {extracted_key}")
                    with open(self.output_file, "w") as file:
                        file.write(extracted_key)
                    logger.info(f"[INFO] Kunci enkripsi disimpan di {self.output_file}")
                    return extracted_key
                logger.warning("[WARNING] Tidak ada teks yang ditemukan dalam EditText.")
            else:
                logger.warning("[ERROR] Tidak ada elemen EditText yang ditemukan.")
        except Exception as e:
            logger.error(f"[ERROR] Terjadi kesalahan saat mengekstrak kunci enkripsi: {e}")
        return None

    def _pick_newest_remote_file(self, found_files):
        if not found_files:
            return None
        if len(found_files) == 1:
            return found_files[0]

        files_quoted = " ".join([f"'{f}'" for f in found_files])
        ls_cmd = f'adb shell "ls -t {files_quoted}"'
        res_ls = subprocess.run(ls_cmd, shell=True, capture_output=True, text=True)
        newest = [line.strip() for line in res_ls.stdout.split('\n') if line.strip()]
        return newest[0] if newest else found_files[0]

    def _filter_db_files_for_account(self, found_files):
        if not found_files:
            return found_files

        if self.account_suffix == "_account2":
            account_files = [f for f in found_files if "/accounts/" in f]
            if account_files:
                logger.info(f"[INFO] Menggunakan database akun kedua dari path accounts/ ({len(account_files)} kandidat)")
                return account_files

        if self.account_suffix == "_account1":
            primary_files = [f for f in found_files if "/accounts/" not in f]
            if primary_files:
                logger.info(f"[INFO] Menggunakan database akun pertama ({len(primary_files)} kandidat)")
                return primary_files

        if self.account_suffix == "_business":
            business_files = [
                f for f in found_files
                if self.package_name in f or "WhatsApp Business" in f
            ]
            if business_files:
                logger.info(f"[INFO] Menggunakan database WhatsApp Business ({len(business_files)} kandidat)")
                return business_files

        return found_files

    def pull_whatsapp_database(self):
        try:
            logger.info("[INFO] Mencari file database WhatsApp secara dinamis...")
            
            # Cari semua file msgstore.db.crypt* di seluruh penyimpanan internal
            find_cmd = 'adb shell "find /storage/emulated/ -type f -name \'msgstore.db.crypt*\' 2>/dev/null"'
            res = subprocess.run(find_cmd, shell=True, capture_output=True, text=True)
            
            found_files = [line.strip() for line in res.stdout.split('\n') if line.strip() and 'msgstore.db.crypt' in line]
            
            # Filter berdasarkan nama paket agar tidak tertukar antara WA Biasa dan Bisnis
            found_files = [f for f in found_files if self.package_name in f]
            
            # Prioritaskan penyimpanan utama (user 0) untuk menghindari nyasar ke Dual Messenger (user 95 dsb)
            primary_files = [f for f in found_files if f.startswith('/storage/emulated/0/')]
            if primary_files:
                found_files = primary_files

            found_files = self._filter_db_files_for_account(found_files)
            
            if not found_files:
                logger.warning("[ERROR] File msgstore.db.crypt14/15 tidak ditemukan di perangkat.")
            else:
                remote_db = self._pick_newest_remote_file(found_files)
    
                adb_command = ["adb", "pull", remote_db, self.database_file]
                
                logger.info(f"[INFO] Mengunduh file database WhatsApp ({remote_db})...")
                result = subprocess.run(adb_command, capture_output=True, text=True)
    
                if result.returncode == 0:
                    logger.info("[SUCCESS] File database berhasil diunduh!")
                    logger.info(f"[INFO] Lokasi: {self.database_file}")
                else:
                    logger.warning(f"[ERROR] Gagal mengunduh file database. Pesan kesalahan: {result.stderr}")

            # Cari semua file wa.db.crypt*
            find_wa_cmd = 'adb shell "find /storage/emulated/ -type f -name \'wa.db.crypt*\' 2>/dev/null"'
            res_wa = subprocess.run(find_wa_cmd, shell=True, capture_output=True, text=True)
            found_wa_files = [line.strip() for line in res_wa.stdout.split('\n') if line.strip() and 'wa.db.crypt' in line]
            
            # Filter berdasarkan nama paket
            found_wa_files = [f for f in found_wa_files if self.package_name in f]
            
            primary_wa_files = [f for f in found_wa_files if f.startswith('/storage/emulated/0/')]
            if primary_wa_files:
                found_wa_files = primary_wa_files

            found_wa_files = self._filter_db_files_for_account(found_wa_files)
            
            if found_wa_files:
                remote_wa_db = self._pick_newest_remote_file(found_wa_files)
                
                adb_wa_command = ["adb", "pull", remote_wa_db, self.wa_database_file]
                logger.info(f"[INFO] Mengunduh file database WhatsApp contacts ({remote_wa_db})...")
                result_wa = subprocess.run(adb_wa_command, capture_output=True, text=True)
                if result_wa.returncode == 0:
                    logger.info("[SUCCESS] File database contacts berhasil diunduh!")
                else:
                    logger.warning(f"[ERROR] Gagal mengunduh file database contacts. Pesan kesalahan: {result_wa.stderr}")
            else:
                logger.warning("[WARNING] File wa.db.crypt14/15 tidak ditemukan di perangkat.")
                
        except Exception as e:
            logger.error(f"[ERROR] Terjadi kesalahan saat menarik database WhatsApp: {e}")

    def read_encryption_key(self):
        try:
            with open(self.output_file, "r") as file:
                key = file.read().strip()
            return key
        except FileNotFoundError:
            logger.error(f"[ERROR] File kunci tidak ditemukan: {self.output_file}")
            return None
        except Exception as e:
            logger.error(f"[ERROR] Gagal membaca kunci enkripsi: {e}")
            return None

    def decrypt_whatsapp_db(self):
        encryption_key = self.read_encryption_key()
        if encryption_key is None:
            logger.error("[ERROR] Tidak bisa melanjutkan dekripsi karena kunci tidak ditemukan.")
            return

        if not encryption_key or len(encryption_key) not in (64, 131):
            logger.error("[ERROR] Kunci enkripsi tidak valid atau kosong. Harap extract ulang kunci enkripsi.")
            return

        decrypted_db_dir = account_db_dir(self.device_id, self.account_suffix)
        decrypted_db_path = decrypted_db_file(self.device_id, self.account_suffix)

        if not os.path.exists(decrypted_db_dir):
            logger.info(f"[INFO] Direktori '{decrypted_db_dir}' tidak ditemukan, membuat direktori...")
            os.makedirs(decrypted_db_dir, exist_ok=True)

        if os.path.exists(decrypted_db_path):
            logger.info(f"[INFO] File database hasil dekripsi lama sudah ada: {decrypted_db_path}, akan ditimpa dengan yang terbaru.")
        else:
            logger.info(f"[INFO] File database hasil decrypt belum ada: {decrypted_db_path}")

        script_path = os.path.join(os.path.dirname(__file__), "decrypt-wa.py")
        msgstore_decrypted = False

        if os.path.exists(self.database_file):
            command = [sys.executable, script_path, "--force", encryption_key, self.database_file, decrypted_db_path]
            try:
                result = subprocess.run(command, capture_output=True, text=True, check=True)
                logger.info("[SUCCESS] Decryption msgstore Output:")
                logger.info(result.stdout)

                if os.path.exists(self.database_file):
                    os.remove(self.database_file)

                if os.path.isfile(decrypted_db_path) and os.path.getsize(decrypted_db_path) > 0:
                    msgstore_decrypted = True
            except subprocess.CalledProcessError as e:
                logger.error("[ERROR] Gagal mendekripsi database WhatsApp.")
                logger.error(f"[ERROR] Pesan kesalahan: {e.stdout}\n{e.stderr}")
        else:
            logger.warning(f"[WARNING] File ciphertext tidak ditemukan: {self.database_file}, skip dekripsi msgstore.")

        if os.path.exists(self.wa_database_file):
            decrypted_wa_path = decrypted_wa_db_file(self.device_id, self.account_suffix)
            command_wa = [sys.executable, script_path, "--force", encryption_key, self.wa_database_file, decrypted_wa_path]
            try:
                result_wa = subprocess.run(command_wa, capture_output=True, text=True, check=True)
                logger.info("[SUCCESS] Decryption wa.db Output:")
                logger.info(result_wa.stdout)

                if os.path.exists(self.wa_database_file):
                    os.remove(self.wa_database_file)
            except subprocess.CalledProcessError as e:
                logger.error("[ERROR] Gagal mendekripsi wa.db.crypt.")
                logger.error(f"[ERROR] Pesan kesalahan: {e.stdout}\n{e.stderr}")

        if msgstore_decrypted:
            pull_wa_dir = pull_account_dir(self.device_id, self.account_suffix)
            if cleanup_pull_account_dir(self.device_id, self.account_suffix):
                logger.info(f"[INFO] Folder pull dihapus setelah DB dipindah ke db/: {pull_wa_dir}")

    def cleanup_files(self):
        try:
            if os.path.exists(self.output_file):
                os.remove(self.output_file)
                logger.info(f"[INFO] File {self.output_file} dihapus.")
            if os.path.exists(self.database_file):
                os.remove(self.database_file)
                logger.info(f"[INFO] File {self.database_file} dihapus.")
            if os.path.exists(self.wa_database_file):
                os.remove(self.wa_database_file)
                logger.info(f"[INFO] File {self.wa_database_file} dihapus.")
        except Exception as e:
            logger.error(f"[ERROR] Gagal menghapus file: {e}")
    
    def cleanup_files_db_backup(self):
        try:
            if os.path.exists( self.backup_db):
                os.remove( self.backup_db)
                logger.info(f"[INFO] File { self.backup_db} dihapus.")
        except Exception as e:
            logger.error(f"[ERROR] Gagal menghapus file: {e}")

#
