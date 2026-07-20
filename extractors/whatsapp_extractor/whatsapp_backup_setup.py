import os
import uiautomator2 as u2
import time
import sys
import subprocess
from extract_keys_wa import WhatsappTools
import logging

from merge_dbs_sqlite import MergeDB
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

class WhatsAppAutomation:
    def __init__(self):
        try:
            self.device_id = self.get_connected_device()
            if not self.device_id:
                raise ConnectionError("Tidak ada perangkat yang terhubung melalui ADB.")
                
            self.d = u2.connect(self.device_id)
            self.extract_wa = WhatsappTools()
            if not self.d.info:
                raise ConnectionError("[Failed] Gagal terhubung ke perangkat.")
                
            self.packageName = "com.whatsapp"
            self.merge_db = MergeDB()
            
            # Cek tipe HP (Samsung atau bukan)
            self.check_device_brand()
        except Exception as e:
            logging.error(f"[Error] saat menghubungkan ke perangkat: {e}")
            sys.exit(1)

    def check_device_brand(self):
        try:
            result = subprocess.run(["adb", "-s", str(self.device_id), "shell", "getprop", "ro.product.manufacturer"], capture_output=True, text=True, check=True)
            manufacturer = result.stdout.strip().lower()
            if "samsung" in manufacturer:
                logging.info(f"[INFO] Perangkat terdeteksi sebagai Samsung ({manufacturer}).")
            else:
                logging.info(f"[INFO] Perangkat terdeteksi bukan Samsung ({manufacturer}). Menjalankan getevent -lt...")
                # Menjalankan getevent secara asynchronous agar tidak memblokir script utama
                subprocess.Popen(["adb", "-s", str(self.device_id), "shell", "getevent", "-lt"])
        except Exception as e:
            logging.error(f"[Error] Gagal mengecek merek HP: {e}")

    def check_adb(self):
        logging.info(f"-" * 48)
        logging.info("Copyright © 2025 4n6 . All rights reserved")
        logging.info("-" * 48)
        try:
            subprocess.run(["adb", "version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            logging.info("Command is running...")
        except Exception:
            logging.info("Please check the USB cable.")
    
    def get_connected_device(self):
        self.check_adb()
        time.sleep(1)
        try:
            result = subprocess.run(["adb", "devices"], capture_output=True, text=True)
            lines = result.stdout.split("\n")[1:]
            devices = [line.split("\t")[0] for line in lines if "device" in line]

            return devices[0] if devices else None
        except Exception as e:
            logging.error(f"[Error] saat mendeteksi perangkat ADB: {e}")
            return None

    def is_screen_on(self):
        try:
            result = subprocess.run(
                ["adb", "shell", "dumpsys", "power"],
                capture_output=True,
                text=True,
                check=True
            )
            output = result.stdout

            if "Display Power: state=ON" in output or "mScreenOn=true" in output or "mWakefulness=Awake" in output:
                return True
            else:
                return False
        except subprocess.CalledProcessError as e:
            logging.error(f"[ERROR] Gagal mengecek status layar: {e}")
            return False

    def swipe_up(self):
        try:
            subprocess.run(["adb", "shell", "input", "swipe", "500", "1800", "500", "300"], check=True)
            logging.info("[INFO] Swipe berhasil dijalankan.")
        except subprocess.CalledProcessError as e:
            logging.error(f"[ERROR] Gagal melakukan swipe: {e}")

    def wake_and_swipe(self):
        try:
            if self.is_screen_on():
                logging.info("[INFO] Layar sudah menyala. Langsung swipe.")
                self.swipe_up()
            else:
                logging.info("[INFO] Layar mati. Menyalakan layar terlebih dahulu.")
                try:
                    subprocess.run(["adb", "shell", "input", "keyevent", "KEYCODE_WAKEUP"], check=True)
                    logging.info("[INFO] Layar dinyalakan.")
                    time.sleep(1.5)
                    self.swipe_up()
                except subprocess.CalledProcessError as e:
                    logging.error(f"[ERROR] Gagal menyalakan layar: {e}")
        except Exception as e:
            logging.error(f"[ERROR] Terjadi kesalahan tak terduga: {e}")

    def open_recent_apps(self):
        self.wake_and_swipe()
        time.sleep(2)
        self.close_history_apps()
        time.sleep(1)
        try:
            recent_apps_button = self.d(resourceId="com.android.systemui:id/recent_apps")
            if recent_apps_button.exists(timeout=1):
                recent_apps_button.click(timeout=1)
                logging.info("[Success] Recent Apps berhasil dibuka.")
                time.sleep(1)
                self.close_history_apps()
                time.sleep(1)
            else:
                logging.warning("[Failed] Recent Apps tidak ditemukan.")
        except Exception as e:
            logging.error(f"[Error] Terjadi kesalahan saat membuka Recent Apps: {e}")

    def close_history_apps(self):
        try:
            clear_all_button = self.d.xpath('//*[@resource-id="com.sec.android.app.launcher:id/clear_all"]')
            miui_clear_button = self.d.xpath('//*[@resource-id="com.miui.home:id/clearAnimView"]')
            clear_all_button_alt = self.d.xpath('//*[@resource-id="com.sec.android.app.launcher:id/clear_all_button"]') # Optional alternative ID
            
            if clear_all_button.exists:
                clear_all_button.click()
                time.sleep(1)
                logging.info("[Success] Semua aplikasi di Recent Apps telah ditutup (Samsung).")
            elif clear_all_button_alt.exists:
                clear_all_button_alt.click()
                time.sleep(1)
                logging.info("[Success] Semua aplikasi di Recent Apps telah ditutup (Samsung alt).")
            elif miui_clear_button.exists:
                miui_clear_button.click()
                time.sleep(1)
                logging.info("[Success] Semua aplikasi di Recent Apps telah ditutup (Xiaomi).")
            else:
                logging.warning("[Failed] Tombol 'Clear All' tidak ditemukan.")
                
            subprocess.run(["adb", "-s", str(self.device_id), "shell", "am", "force-stop", "com.whatsapp"], check=False)
            logging.info("[Success] Fallback: Memastikan WhatsApp ditutup secara paksa (Universal).")
        except Exception as e:
            logging.error(f"[Error] path close all apps: {e}")

    def backup_chat(self):
        try:
            if self.packageName not in self.d.app_list():
                raise ValueError("WhatsApp tidak terinstal pada perangkat.")

            self.d.app_start(self.packageName, wait=False)
            logging.debug("[Debug] WhatsApp berjalan di latar belakang.")

            time.sleep(2)
            self.open_whatsapp_menu()
            time.sleep(2)
            self.settings_whatsapp()
            time.sleep(2)
            self.menu_chats()
            time.sleep(3)

            logging.info("[Success] Proses pengaturan cadangan terenkripsi selesai.")
        except Exception as e:
            logging.error(f"[Error] Terjadi kesalahan saat membuka WhatsApp: {e}")

    def open_whatsapp_menu(self):
        try:
            menu_button = self.d.xpath('//*[@resource-id="com.whatsapp:id/menuitem_overflow"]')
            if menu_button.exists:
                menu_button.click()
                logging.info("[Success] Menu overflow di WhatsApp berhasil dibuka.")
            else:
                logging.warning("[Failed] Menu overflow di WhatsApp tidak ditemukan.")
        except Exception as e:
            logging.error(f"[Error] Terjadi kesalahan saat membuka menu overflow WhatsApp: {e}")

    def settings_whatsapp(self):
        try:
            list_item = self.d.xpath('//android.widget.ListView/android.widget.LinearLayout[7]/android.widget.LinearLayout[1]/android.widget.RelativeLayout[1]')
            if list_item.exists:
                list_item.click()
                logging.info("[Success] click setting success")
                time.sleep(1)
            else:
                fallback_item = self.d.xpath('//*[@resource-id="com.whatsapp:id/menuitem_overflow"]')
                if fallback_item.exists:
                    fallback_item.click()
                    logging.info("[Success] click setting success (menggunakan fallback menuitem_overflow)")
                    time.sleep(1)
                else:
                    logging.warning("[Failed] click setting not found")
        except Exception as e:
            logging.error(f"[Error] Terjadi kesalahan saat memilih settings: {e}")

    def menu_chats(self):
        try:
            logging.debug("[*] Mencari tombol 'Chats'...")

            check_menu_chat = None
            if self.d(resourceId="com.whatsapp:id/row_text", text="Chat").exists:
                check_menu_chat = self.d(resourceId="com.whatsapp:id/row_text", text="Chat")
            elif self.d(resourceId="com.whatsapp:id/row_text", text="Chats").exists:
                check_menu_chat = self.d(resourceId="com.whatsapp:id/row_text", text="Chats")

            if not check_menu_chat:
                logging.warning("[Error] Tombol menu 'Chat' atau 'Chats' tidak ditemukan.")
                return

            while True:
                if check_menu_chat.exists:
                    check_menu_chat.click(timeout=2)
                    logging.info("[Success] Tombol menu 'Chats' berhasil diklik.")
                    time.sleep(1)
                    self.swipe_up()
                    time.sleep(1)
                    break
                else:
                    logging.info("[Info] Tombol 'Chats' belum ditemukan, mencoba lagi...")
                    time.sleep(1)

        except Exception as e:
            logging.error(f"[Error] Gagal menjalankan menu_chats: {e}")

    def swipe_up(self):
        try:
            subprocess.run(["adb", "-s", str(self.device_id), "shell", "input", "swipe", "500", "1500", "500", "300", "500"], check=True)
            logging.info("[Success] Swipe ke atas (dari bawah ke atas) berhasil dijalankan via ADB.")
        except Exception as e:
            logging.error(f"[ERROR] Terjadi kesalahan saat swipe ke atas: {e}")

    def chat_backup_preference(self):
        try:
            chat_backup = self.d.xpath('//*[@resource-id="com.whatsapp:id/chat_backup_preference"]/android.widget.LinearLayout[1]')
            if not chat_backup.exists:
                logging.info("[Info] Elemen chat_backup_preference tidak ditemukan, mencoba elemen alternatif settings_gdrive_e2e_encryption")
                chat_backup = self.d.xpath('//*[@resource-id="com.whatsapp:id/settings_gdrive_e2e_encryption"]/android.widget.LinearLayout[1]/android.widget.LinearLayout[1]')

            if chat_backup.exists:
                chat_backup.click(timeout=2)
                time.sleep(1)
                logging.info("[Success] Berhasil klik cadangan chat")
                self.swipe_up()
                time.sleep(1)
                self.swipe_up()
                time.sleep(1)

                self.check_and_enable_encryption()
                time.sleep(1)
            else:
                logging.warning("[Failed] Gagal klik cadangkan chat, kedua elemen tidak ditemukan")
        except Exception as e:
            logging.error(f"[Error] chat backup preference: {e}")

    def check_and_enable_encryption(self):
        try:
            logging.debug("[*] Mengecek status enkripsi...")

            def get_encryption_status():
                for _ in range(2):
                    if self.d(resourceId="com.whatsapp:id/row_subtext", text="Nyala").exists:
                        return "Nyala"
                    elif self.d(resourceId="com.whatsapp:id/row_subtext", text="On").exists:
                        return "On"
                    elif self.d(resourceId="com.whatsapp:id/row_subtext", text="Mati").exists:
                        return "Mati"
                    elif self.d(resourceId="com.whatsapp:id/row_subtext", text="Off").exists:
                        return "Off"
                    
                    try:
                        for i in range(self.d(resourceId="com.whatsapp:id/row_subtext").count):
                            text = self.d(resourceId="com.whatsapp:id/row_subtext")[i].info.get("text", "").strip().lower()
                            if text in ["nyala", "on", "turned on", "enabled", "aktif"]:
                                return "Nyala"
                            if text in ["mati", "off", "turned off", "disabled", "tidak aktif"]:
                                return "Mati"
                    except Exception as e:
                        logging.debug(f"[Debug] Fallback check status error: {e}")

                    logging.info("[Info] Status enkripsi belum terlihat, scroll ke bawah sedikit...")
                    self.swipe_up()
                    time.sleep(2)
                return None

            status = get_encryption_status()
            if status is None:
                logging.warning("[Error] Tidak ditemukan status enkripsi 'Nyala', 'On', 'Mati', atau 'Off'")
                return

            logging.debug(f"[Debug] Status enkripsi saat ini: {status}")
            encryption_button = None
            if self.d(resourceId="com.whatsapp:id/row_text", text="Cadangan terenkripsi end-to-end").exists:
                encryption_button = self.d(resourceId="com.whatsapp:id/row_text", text="Cadangan terenkripsi end-to-end")
            elif self.d(resourceId="com.whatsapp:id/row_text", text="End-to-end encrypted backup").exists:
                encryption_button = self.d(resourceId="com.whatsapp:id/row_text", text="End-to-end encrypted backup")
            elif self.d(resourceId="com.whatsapp:id/row_text", textMatches="(?i).*encrypted backup.*").exists:
                encryption_button = self.d(resourceId="com.whatsapp:id/row_text", textMatches="(?i).*encrypted backup.*")
            elif self.d(resourceId="com.whatsapp:id/row_text", textMatches="(?i).*cadangan terenkripsi.*").exists:
                encryption_button = self.d(resourceId="com.whatsapp:id/row_text", textMatches="(?i).*cadangan terenkripsi.*")

            if not encryption_button:
                logging.warning("[Error] Tombol enkripsi tidak ditemukan.")
                return

            disable_button = self.d(resourceId="com.whatsapp:id/enc_backup_enabled_landing_disable_button")
            forgot_key_button = self.d(resourceId="com.whatsapp:id/enc_backup_encryption_key_input_forgot")
            confirm_disable_button = self.d(resourceId="com.whatsapp:id/confirm_disable_disable_button")
            disable_done_button = self.d(resourceId="com.whatsapp:id/disable_done_done_button")
            use_encryption_key_button = self.d(resourceId="com.whatsapp:id/enable_education_use_encryption_key_button")
            encryption_key_info_button = self.d(resourceId="com.whatsapp:id/encryption_key_info_bottom_button")
            encryption_key_confirm_button = self.d(resourceId="com.whatsapp:id/encryption_key_confirm_button_confirm")
            enable_done_create_button = self.d(resourceId="com.whatsapp:id/enable_done_create_button")

            if status in ["Nyala", "On"]:
                db_path = f"extractors/whatsapp_extractor/db_whatsapp/{self.device_id}/{self.device_id}.db"
                wa_path = f"extractors/whatsapp_extractor/db_whatsapp/{self.device_id}/wa.db"
                if os.path.exists(db_path) and os.path.exists(wa_path):
                    logging.info(f"[Info] Enkripsi sudah aktif dan kedua database ({self.device_id}.db & wa.db) ditemukan. Menggunakan {self.device_id}_key.txt yang sudah ada.")
                    
                    backup_now_btn = self.d(resourceId="com.whatsapp:id/google_drive_backup_now_btn")
                    if backup_now_btn.exists:
                        backup_now_btn.click()
                        logging.info("[Success] Tombol Backup Now ditekan.")
                        time.sleep(2)
                    else:
                        logging.warning("[Warning] Tombol Backup Now tidak ditemukan.")
                    
                    self.wait_for_cancel_download()
                    return
                else:
                    logging.info(f"[Info] Enkripsi aktif tetapi database belum lengkap ({self.device_id}.db / wa.db belum ada). Menonaktifkan enkripsi untuk generate key baru...")
                    encryption_button.click()
                    time.sleep(1)
                    disable_button.click()
                    time.sleep(1)
                    forgot_key_button.click()
                    time.sleep(1)
                    confirm_disable_button.click()
                    time.sleep(1)
                    disable_done_button.click()
                    time.sleep(1)

                    while True:
                        time.sleep(2)
                        self.extract_wa.extract_whatsapp_keys()
                        logging.info("[Success] Proses ekstrak encryption key sementara berhasil")

                        status = get_encryption_status()
                        if status in ["Mati", "Off"]:
                            logging.info("[Success] Enkripsi berhasil dinonaktifkan sementara.")
                            break

            if status in ["Mati", "Off"]:
                logging.info("[Info] Mengaktifkan kembali enkripsi end-to-end...")
                encryption_button.click()
                time.sleep(1)
                self.enable_encryption()
                time.sleep(1)
                
                more_options_button = self.d(resourceId="com.whatsapp:id/enable_info_more_options_button")
                if more_options_button.exists(timeout=5):
                    more_options_button.click(timeout=3)
                    logging.info("[Success] Berhasil klik enable_info_more_options_button")
                    time.sleep(1)
                else:
                    logging.warning("[Warning] enable_info_more_options_button tidak ditemukan.")
                
                if use_encryption_key_button.exists:
                    use_encryption_key_button.click()
                else:
                    alt_key_button = self.d.xpath('//*[@resource-id="com.whatsapp:id/enc_backup_more_options_encryption_key"]/android.widget.LinearLayout[1]')
                    if alt_key_button.exists:
                        alt_key_button.click()
                    else:
                        logging.warning("[Warning] Tombol penggunaan encryption key tidak ditemukan.")

                logging.info("[Info] Menggunakan kunci enkripsi 64 digit.")
                time.sleep(2)
                encryption_key_info_button.click()
                logging.info("[Info] Membuat kunci 64 digit.")
                time.sleep(1)
                self.extract_wa.extract_whatsapp_keys()
                logging.info("[Success] Proses ekstrak encryption berhasil")
                time.sleep(1)
                encryption_key_info_button.click()
                time.sleep(1)
                encryption_key_confirm_button.click()
                logging.info("[Success] Berhasil menyiapkan kunci 64 digit")
                time.sleep(1)
                enable_done_create_button.click()
                logging.info("[Success] Enkripsi end-to-end berhasil diaktifkan.")
                time.sleep(2)
                self.wait_for_cancel_download()
                time.sleep(2)
                self.open_recent_apps()
                time.sleep(2)
                # self.extract_wa.cleanup_files()
                time.sleep(2)

        except Exception as e:
            logging.error(f"[Error] Terjadi kesalahan saat memeriksa enkripsi: {e}")

    def enable_encryption(self):
        try:
            enable_encryption_button = self.d(resourceId="com.whatsapp:id/enable_info_turn_on_button")
            if enable_encryption_button.exists:
                # enable_encryption_button.click() # Dihapus sesuai permintaan user agar tidak diklik
                logging.debug(f"[Debug] Melewati klik tombol Turn On (menunggu klik more_options_button)")
                time.sleep(1)
            else:
                logging.warning(f"[Failed] gagal menyalakan cadangan data")
        except Exception as e:
            logging.error("[Error] enable encryption: {e}")
            
    def wait_for_cancel_download(self):
        try:
            logging.info("[Waiting] Menunggu proses backup merespons...")
            # Tunggu maksimal 10 detik sampai tombol cancel (X) muncul
            self.d(resourceId="com.whatsapp:id/cancel_download").wait(timeout=10.0)
            
            if self.d(resourceId="com.whatsapp:id/cancel_download").exists:
                logging.info("[Waiting] Sedang Proses Backup/Upload...")
                while self.d(resourceId="com.whatsapp:id/cancel_download").exists:
                    time.sleep(2)
                logging.info("[Success] Proses backup selesai!!")
            else:
                logging.info("[Info] Proses backup berlangsung sangat cepat atau sudah selesai.")
                time.sleep(5)

            # Pastikan tombol backup now kembali muncul (standby)
            while not self.d(resourceId="com.whatsapp:id/google_drive_backup_now_btn").exists:
                time.sleep(2)

            logging.info("[Found] Berhasil Backup, melanjutkan proses penarikan data...")
            time.sleep(3)
            self.extract_wa.pull_whatsapp_database()
            time.sleep(3)
            self.extract_wa.decrypt_whatsapp_db()

        except Exception as e:
            logging.error(f"[Error] Terjadi kesalahan saat menunggu elemen: {e}")

    def run_all_automation(self):
        self.open_recent_apps()
        time.sleep(2)
        self.backup_chat()
        time.sleep(1)
        self.chat_backup_preference()
        time.sleep(2)
        
        # Bersihkan recent apps di akhir proses
        logging.info("[Info] Proses selesai. Membersihkan recent apps...")
        self.open_recent_apps()
        time.sleep(2)

if __name__ == "__main__":
    wa_automation = WhatsAppAutomation()
    wa_automation.run_all_automation()
