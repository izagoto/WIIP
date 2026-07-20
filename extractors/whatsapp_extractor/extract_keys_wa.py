import os
import uiautomator2 as u2
import sys
import subprocess
import logging

logger = logging.getLogger(__name__)

class WhatsappTools:
    def __init__(self):
        try:
            logging.info("[INFO] Menghubungkan ke perangkat...")
            self.d = u2.connect()
            if not self.d.info:
                raise ConnectionError("[ERROR] Tidak dapat terhubung ke perangkat.")
            
            self.pull_path = "extractors/whatsapp_extractor/pull"
            os.makedirs(self.pull_path, exist_ok=True)
            
            self.device_id = self.get_device_id()
            self.output_file = f"{self.pull_path}/{self.device_id}_key.txt"
            self.backup_db = f"extractors/whatsapp_extractor/db_backup/{self.device_id}.db"
            self.database_file = f"{self.pull_path}/{self.device_id}.db"
            self.wa_database_file = f"{self.pull_path}/wa.db.crypt"
        except Exception as e:
            logging.info(f"[ERROR] Gagal menghubungkan ke perangkat: {e}")
            sys.exit(1)

    def get_device_id(self):
        try:
            result = subprocess.run(["adb", "devices"], capture_output=True, text=True, check=True)
            devices = result.stdout.strip().split("\n")[1:]
            
            if not devices or devices[0] == "":
                logging.warning("[ERROR] Tidak ada perangkat ADB yang terhubung.")
                sys.exit(1)
            
            device_id = devices[0].split("\t")[0]
            return device_id
        except Exception as e:
            logging.error(f"[ERROR] Gagal mendapatkan device ID: {e}")
            sys.exit(1)

    def extract_whatsapp_keys(self):
        try:
            logging.info("[INFO] Mencari elemen EditText di WhatsApp...")
            edit_text_fields = self.d(className="android.widget.EditText")

            if edit_text_fields.exists:
                keys = [field.get_text().strip() for field in edit_text_fields if field.get_text()]
                extracted_key = "".join(keys)

                if extracted_key:
                    logging.info(f"[SUCCESS] Kunci enkripsi ditemukan: {extracted_key}")
                    with open(self.output_file, "w") as file:
                        file.write(extracted_key)
                    logging.info(f"[INFO] Kunci enkripsi disimpan di {self.output_file}")
                    return extracted_key
                else:
                    logging.warning("[WARNING] Tidak ada teks yang ditemukan dalam EditText.")
            else:
                logging.warning("[ERROR] Tidak ada elemen EditText yang ditemukan.")
        except Exception as e:
            logging.error(f"[ERROR] Terjadi kesalahan saat mengekstrak kunci enkripsi: {e}")

    def pull_whatsapp_database(self):
        try:
            logging.info("[INFO] Mencari file database WhatsApp secara dinamis...")
            
            # Cari semua file msgstore.db.crypt* di seluruh penyimpanan internal
            find_cmd = 'adb shell "find /storage/emulated/ -type f -name \'msgstore.db.crypt*\' 2>/dev/null"'
            res = subprocess.run(find_cmd, shell=True, capture_output=True, text=True)
            
            found_files = [line.strip() for line in res.stdout.split('\n') if line.strip() and 'msgstore.db.crypt' in line]
            
            # Prioritaskan penyimpanan utama (user 0) untuk menghindari nyasar ke Dual Messenger (user 95 dsb)
            primary_files = [f for f in found_files if f.startswith('/storage/emulated/0/')]
            if primary_files:
                found_files = primary_files
            
            if not found_files:
                logging.warning("[ERROR] File msgstore.db.crypt14/15 tidak ditemukan di perangkat.")
            else:
                # Jika ada banyak file, urutkan berdasarkan waktu modifikasi terbaru (menggunakan ls -t di shell adb)
                if len(found_files) > 1:
                    files_quoted = " ".join([f"'{f}'" for f in found_files])
                    ls_cmd = f'adb shell "ls -t {files_quoted}"'
                    res_ls = subprocess.run(ls_cmd, shell=True, capture_output=True, text=True)
                    
                    remote_db = [line.strip() for line in res_ls.stdout.split('\n') if line.strip()][0]
                else:
                    remote_db = found_files[0]
    
                adb_command = f"adb pull '{remote_db}' '{self.database_file}'"
                
                logging.info(f"[INFO] Mengunduh file database WhatsApp ({remote_db})...")
                result = subprocess.run(adb_command, shell=True, capture_output=True, text=True)
    
                if result.returncode == 0:
                    logging.info("[SUCCESS] File database berhasil diunduh!")
                    logging.info(f"[INFO] Lokasi: {self.database_file}")
                else:
                    logging.warning(f"[ERROR] Gagal mengunduh file database. Pesan kesalahan: {result.stderr}")

            # Cari semua file wa.db.crypt*
            find_wa_cmd = 'adb shell "find /storage/emulated/ -type f -name \'wa.db.crypt*\' 2>/dev/null"'
            res_wa = subprocess.run(find_wa_cmd, shell=True, capture_output=True, text=True)
            found_wa_files = [line.strip() for line in res_wa.stdout.split('\n') if line.strip() and 'wa.db.crypt' in line]
            
            primary_wa_files = [f for f in found_wa_files if f.startswith('/storage/emulated/0/')]
            if primary_wa_files:
                found_wa_files = primary_wa_files
            
            if found_wa_files:
                if len(found_wa_files) > 1:
                    files_quoted = " ".join([f"'{f}'" for f in found_wa_files])
                    ls_cmd = f'adb shell "ls -t {files_quoted}"'
                    res_ls = subprocess.run(ls_cmd, shell=True, capture_output=True, text=True)
                    remote_wa_db = [line.strip() for line in res_ls.stdout.split('\n') if line.strip()][0]
                else:
                    remote_wa_db = found_wa_files[0]
                
                adb_wa_command = f"adb pull '{remote_wa_db}' '{self.wa_database_file}'"
                logging.info(f"[INFO] Mengunduh file database WhatsApp contacts ({remote_wa_db})...")
                result_wa = subprocess.run(adb_wa_command, shell=True, capture_output=True, text=True)
                if result_wa.returncode == 0:
                    logging.info("[SUCCESS] File database contacts berhasil diunduh!")
                else:
                    logging.warning(f"[ERROR] Gagal mengunduh file database contacts. Pesan kesalahan: {result_wa.stderr}")
            else:
                logging.warning("[WARNING] File wa.db.crypt14/15 tidak ditemukan di perangkat.")
                
        except Exception as e:
            logging.error(f"[ERROR] Terjadi kesalahan saat menarik database WhatsApp: {e}")

    def read_encryption_key(self):
        try:
            with open(self.output_file, "r") as file:
                key = file.read().strip()
            return key
        except FileNotFoundError:
            logging.error(f"[ERROR] File kunci tidak ditemukan: {self.output_file}")
            return None
        except Exception as e:
            logging.error(f"[ERROR] Gagal membaca kunci enkripsi: {e}")
            return None

    def decrypt_whatsapp_db(self):
        encryption_key = self.read_encryption_key()
        if encryption_key is None:
            logging.error("[ERROR] Tidak bisa melanjutkan dekripsi karena kunci tidak ditemukan.")
            return

        decrypted_db_dir = f"extractors/whatsapp_extractor/db_whatsapp/{self.device_id}"
        decrypted_db_path = f"{decrypted_db_dir}/{self.device_id}.db"

        if not os.path.exists(decrypted_db_dir):
            logging.info(f"[INFO] Direktori '{decrypted_db_dir}' tidak ditemukan, membuat direktori...")
            os.makedirs(decrypted_db_dir, exist_ok=True)

        if os.path.exists(decrypted_db_path):
            logging.info(f"[INFO] File database hasil dekripsi lama sudah ada: {decrypted_db_path}, akan ditimpa dengan yang terbaru.")
        else:
            logging.info(f"[INFO] File database hasil decrypt belum ada: {decrypted_db_path}")

        script_path = os.path.join(os.path.dirname(__file__), "decrypt-wa.py")
        if os.path.exists(self.database_file):
            command = [sys.executable, script_path, "--force", encryption_key, self.database_file, decrypted_db_path]
            try:
                result = subprocess.run(command, capture_output=True, text=True, check=True)
                logging.info("[SUCCESS] Decryption msgstore Output:")
                logging.info(result.stdout)
                
                # Hapus file mentah jika sukses
                if os.path.exists(self.database_file):
                    os.remove(self.database_file)
            except subprocess.CalledProcessError as e:
                logging.error("[ERROR] Gagal mendekripsi database WhatsApp.")
                logging.error(f"[ERROR] Pesan kesalahan: {e.stdout}\n{e.stderr}")
        else:
            logging.warning(f"[WARNING] File ciphertext tidak ditemukan: {self.database_file}, skip dekripsi msgstore.")

        if os.path.exists(self.wa_database_file):
            decrypted_wa_path = f"{decrypted_db_dir}/wa.db"
            command_wa = [sys.executable, script_path, "--force", encryption_key, self.wa_database_file, decrypted_wa_path]
            try:
                result_wa = subprocess.run(command_wa, capture_output=True, text=True, check=True)
                logging.info("[SUCCESS] Decryption wa.db Output:")
                logging.info(result_wa.stdout)
                
                # Hapus file mentah jika sukses
                if os.path.exists(self.wa_database_file):
                    os.remove(self.wa_database_file)
            except subprocess.CalledProcessError as e:
                logging.error("[ERROR] Gagal mendekripsi wa.db.crypt.")
                logging.error(f"[ERROR] Pesan kesalahan: {e.stdout}\n{e.stderr}")

    def cleanup_files(self):
        try:
            if os.path.exists(self.output_file):
                os.remove(self.output_file)
                logging.info(f"[INFO] File {self.output_file} dihapus.")
            if os.path.exists(self.database_file):
                os.remove(self.database_file)
                logging.info(f"[INFO] File {self.database_file} dihapus.")
            if os.path.exists(self.wa_database_file):
                os.remove(self.wa_database_file)
                logging.info(f"[INFO] File {self.wa_database_file} dihapus.")
        except Exception as e:
            logging.error(f"[ERROR] Gagal menghapus file: {e}")
    
    def cleanup_files_db_backup(self):
        try:
            if os.path.exists( self.backup_db):
                os.remove( self.backup_db)
                logging.info(f"[INFO] File { self.backup_db} dihapus.")
        except Exception as e:
            logging.error(f"[ERROR] Gagal menghapus file: {e}")
