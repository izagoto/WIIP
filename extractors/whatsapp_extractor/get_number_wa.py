import uiautomator2 as u2
import time
import sys
import subprocess
from whatsapp_backup_setup import WhatsAppAutomation
import re
import logging

logger = logging.getLogger(__name__)

class GetNumberWA:
    def __init__(self):
        try:
            self.device_id = self.get_connected_device()
            if not self.device_id:
                raise ConnectionError("Tidak ada perangkat yang terhubung melalui ADB.")
                
            self.d = u2.connect(self.device_id)
            self.whatsapp_backup = WhatsAppAutomation()
            if not self.d.info:
                raise ConnectionError("[Failed] Gagal terhubung ke perangkat.")
                
            self.packageName = "com.whatsapp"
        except Exception as e:
            logging.error(f"[Error] saat menghubungkan ke perangkat: {e}")
            sys.exit(1)

    def check_adb(self):
        try:
            subprocess.run(["adb", "version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
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
        
    def open_whatsapp_via_adb(self):
        try:
            logging.info("[INFO] Membuka aplikasi WhatsApp...")
            result = subprocess.run(
                ["adb", "shell", "monkey", "-p", self.packageName, "-c", "android.intent.category.LAUNCHER", "1"],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            if result.returncode == 0:
                time.sleep(3)
                try:
                    if self.d(resourceId="com.whatsapp:id/eula_logo").exists:
                        logging.warning("[WARNING] Akun WhatsApp tidak ditemukan. WhatsApp berada di halaman awal (belum login).")
                        self.whatsapp_backup.open_recent_apps()
                        time.sleep(2)
                        self.whatsapp_backup.close_history_apps()
                        time.sleep(2)
                        return
                    else:
                        logging.info("[SUCCESS] WhatsApp berhasil dibuka dan akun ditemukan.")
                except Exception as e:
                    logging.error(f"[ERROR] Gagal melakukan pengecekan elemen UI: {e}")
            else:
                logging.warning(f"[WARNING] Perintah ADB dijalankan tapi return code bukan 0: {result.returncode}")
                logging.warning(f"[WARNING] Output: {result.stdout}")
                logging.warning(f"[WARNING] Error: {result.stderr}")

        except subprocess.CalledProcessError as e:
            logging.error(f"[ERROR] Gagal membuka WhatsApp. Perintah ADB gagal: {e.stderr}")
        except Exception as e:
            logging.error(f"[ERROR] Terjadi kesalahan saat membuka WhatsApp: {str(e)}")
    
    def click_menu_overflow(self):
        try:
            menu_button = self.d(resourceId="com.whatsapp:id/menuitem_overflow")
            if menu_button.exists(timeout=5):
                menu_button.click()
                logging.info("[SUCCESS] Berhasil klik tombol menu overflow (tiga titik).")
                time.sleep(2)
            else:
                logging.warning("[WARNING] Tombol menu overflow tidak ditemukan.")
        except Exception as e:
            logging.error(f"[ERROR] Gagal klik tombol menu overflow: {e}")
    
    def settings_whatsapp(self):
        try:
            list_item = self.d.xpath('//android.widget.ListView/android.widget.LinearLayout[7]/android.widget.LinearLayout[1]/android.widget.RelativeLayout[1]')
            if list_item.exists:
                list_item.click()
                logging.info("[Success] click setting success")
                time.sleep(1)
            else:
                logging.warning("[Failed] click setting not found")
        except Exception as e:
            logging.error(f"[Error] Terjadi kesalahan saat memilih settings: {e}")

    def tab_profil_info(self):
        self.whatsapp_backup.open_recent_apps()
        time.sleep(2)
        self.whatsapp_backup.close_history_apps()
        time.sleep(2)
        self.open_whatsapp_via_adb()
        time.sleep(2)
        self.click_menu_overflow()
        time.sleep(2)
        self.settings_whatsapp()
        time.sleep(2)
        try:
            info_profil = self.d(resourceId="com.whatsapp:id/profile_info_photo")
            if info_profil.exists:
                info_profil.click()
                logging.info(f"[Success] Berhasil klik info profil WhatsApp")
                time.sleep(2)
                self.get_number_whatsapp()
                time.sleep(2)
            else:
                logging.warning(f"[Failed] Gagal klik info profil WhatsApp")
        except Exception as e:
            logging.error(f"[Error] terjadi kesalahan saat membuka profil WhatsApp: {e}")
    
    def get_number_whatsapp(self):
        try:
            number_element = self.d.xpath('//*[@resource-id="com.whatsapp:id/profile_phone_info"]//android.widget.TextView[@resource-id="com.whatsapp:id/profile_settings_row_subtext"]')

            if number_element.exists:
                number_text = number_element.get_text()
                normalized_number = re.sub(r"[^\d+]", "", number_text or "")
                print(f"{normalized_number}")
                return normalized_number
            else:
                logging.warning("[WARNING] Tidak dapat menemukan elemen nomor WhatsApp.")
                return None

        except Exception as e:
            logging.error(f"[ERROR] Terjadi kesalahan saat mengambil nomor WhatsApp: {e}")
            return None

    def main(self):
        self.tab_profil_info()
        time.sleep(2)

if __name__ == "__main__":
    app = GetNumberWA()
    app.main()
