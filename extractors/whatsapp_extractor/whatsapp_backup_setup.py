import os
import uiautomator2 as u2
import time
import sys
import subprocess
from extract_keys_wa import WhatsappTools
import logging

from merge_dbs_sqlite import MergeDB
from paths import account_key_dir, key_file
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

class WhatsAppAutomation:
    def __init__(self):
        try:
            self.device_id = self.get_connected_device()
            if not self.device_id:
                raise ConnectionError("Tidak ada perangkat yang terhubung melalui ADB.")
                
            self.d = u2.connect(self.device_id)
            if not self.d.info:
                raise ConnectionError("[Failed] Gagal terhubung ke perangkat.")
                
            self.merge_db = MergeDB()
            self.packageName = "com.whatsapp"

            # Cek tipe HP (Samsung atau bukan)
            self.check_device_brand()
        except Exception as e:
            logging.error(f"[Error] saat menghubungkan ke perangkat: {e}")
            sys.exit(1)

    def check_device_brand(self):
        try:
            res_manuf = subprocess.run(["adb", "-s", str(self.device_id), "shell", "getprop", "ro.product.manufacturer"], capture_output=True, text=True, check=True)
            manufacturer = res_manuf.stdout.strip()
            
            res_model = subprocess.run(["adb", "-s", str(self.device_id), "shell", "getprop", "ro.product.model"], capture_output=True, text=True, check=True)
            model = res_model.stdout.strip()
            
            res_ver = subprocess.run(["adb", "-s", str(self.device_id), "shell", "getprop", "ro.build.version.release"], capture_output=True, text=True, check=True)
            android_ver = res_ver.stdout.strip()
            
            if "samsung" in manufacturer.lower():
                logging.info(f"[INFO] Perangkat terdeteksi sebagai {manufacturer} {model} [Android {android_ver}] dengan serial number {self.device_id}.")
            else:
                logging.info(f"[INFO] Perangkat terdeteksi sebagai {manufacturer} {model} [Android {android_ver}] dengan serial number {self.device_id}. Menjalankan getevent -lt...")
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
                
            subprocess.run(["adb", "-s", str(self.device_id), "shell", "am", "force-stop", self.packageName], check=False)
            logging.info(f"[Success] Fallback: Memastikan {self.packageName} ditutup secara paksa.")
        except Exception as e:
            logging.error(f"[Error] path close all apps: {e}")

    def _ensure_app_foreground(self):
        logging.info(f"[INFO] Membuka aplikasi {self.packageName}...")
        self.d.app_start(self.packageName, wait=True)
        time.sleep(3)
        current = self.d.app_current()
        active_package = current.get("package") if current else None
        if active_package != self.packageName:
            logging.warning(f"[Warning] Package aktif '{active_package}' bukan '{self.packageName}', mencoba lagi...")
            subprocess.run(
                ["adb", "-s", str(self.device_id), "shell", "monkey", "-p", self.packageName, "-c", "android.intent.category.LAUNCHER", "1"],
                check=False,
                capture_output=True,
            )
            time.sleep(3)
        return True

    def backup_chat(self):
        try:
            if self.packageName not in self.d.app_list():
                raise ValueError("WhatsApp tidak terinstal pada perangkat.")

            self._ensure_app_foreground()
            self.settings_whatsapp()
            time.sleep(2)
            self.open_whatsapp_menu()
            time.sleep(2)
            self.menu_chats()
            time.sleep(3)

            logging.info("[Success] Proses pengaturan cadangan terenkripsi selesai.")
        except Exception as e:
            logging.error(f"[Error] Terjadi kesalahan saat membuka WhatsApp: {e}")

    def open_whatsapp_menu(self):
        try:
            menu_button = self.d.xpath(f'//*[@resource-id=\"{self.packageName}:id/menuitem_overflow"]')
            if menu_button.exists:
                menu_button.click()
                time.sleep(1)
                logging.info("[Success] Menu overflow di WhatsApp berhasil dibuka.")
                return True
            logging.warning("[Failed] Menu overflow di WhatsApp tidak ditemukan.")
            return False
        except Exception as e:
            logging.error(f"[Error] Terjadi kesalahan saat membuka menu overflow WhatsApp: {e}")
            return False

    def _get_listview_item_text(self, index):
        texts = []
        base_xpath = f'//android.widget.ListView/android.widget.LinearLayout[{index}]'
        item = self.d.xpath(base_xpath)
        if not item.exists:
            return ""

        info = item.info
        if info.get("text"):
            texts.append(str(info.get("text")).strip())

        for j in range(1, 6):
            text_node = self.d.xpath(f'{base_xpath}//android.widget.TextView[{j}]')
            if not text_node.exists:
                break
            text_value = (text_node.info.get("text") or "").strip()
            if text_value:
                texts.append(text_value)

        desc = (info.get("contentDescription") or "").strip()
        if desc:
            texts.append(desc)

        return " ".join(texts).lower()

    def _find_switch_account_button(self):
        switch_keywords = [
            "switch account",
            "beralih akun",
            "alihkan akun",
            "ganti akun",
            "tukar akun",
        ]

        parent_text_xpaths = [
            '//*[@text="Switch account" or @text="Beralih akun" or @text="Alihkan akun" or @text="Ganti akun" or @text="Tukar akun"]/ancestor::android.widget.LinearLayout[1]',
            '//*[contains(@text, "Switch account") or contains(@text, "Beralih akun") or contains(@text, "Alihkan akun")]/ancestor::android.widget.LinearLayout[1]',
            '//*[@content-desc="Switch account" or @content-desc="Beralih akun" or @content-desc="Alihkan akun"]/ancestor::android.widget.LinearLayout[1]',
        ]
        for xpath in parent_text_xpaths:
            parent = self.d.xpath(xpath)
            if parent.exists:
                logging.info("[Found] Menu switch account via teks child + parent LinearLayout")
                return parent

        text_xpath_candidates = [
            '//*[@text="Switch account" or @text="Beralih akun" or @text="Alihkan akun" or @text="Ganti akun" or @text="Tukar akun"]',
            '//*[contains(@text, "Switch account") or contains(@text, "Beralih akun") or contains(@text, "Alihkan akun")]',
            '//*[@content-desc="Switch account" or @content-desc="Beralih akun" or @content-desc="Alihkan akun"]',
        ]
        for xpath in text_xpath_candidates:
            text_elem = self.d.xpath(xpath)
            if text_elem.exists:
                logging.info("[Found] Menu switch account via teks langsung")
                return text_elem

        switch_labels = [
            "Switch account",
            "Beralih akun",
            "Alihkan akun",
            "Ganti akun",
            "Tukar akun",
        ]
        for label in switch_labels:
            for selector in (
                self.d(text=label),
                self.d(description=label),
                self.d(textContains=label),
            ):
                if selector.exists:
                    logging.info(f"[Found] Menu switch account via selector '{label}'")
                    return selector

        # Layout A: Switch account langsung di item ke-7 (tanpa Settings)
        # Layout B: Settings di item ke-7, Switch account di item ke-8
        layout_candidates = [8, 7, 9]
        for index in layout_candidates:
            item = self.d.xpath(f'//android.widget.ListView/android.widget.LinearLayout[{index}]')
            if not item.exists:
                continue
            combined_text = self._get_listview_item_text(index)
            logging.debug(f"[Debug] Menu item [{index}]: '{combined_text}'")
            if any(keyword in combined_text for keyword in switch_keywords):
                logging.info(f"[Found] Menu switch account via ListView LinearLayout[{index}]")
                return item

        try:
            for i in range(1, 15):
                item = self.d.xpath(f'//android.widget.ListView/android.widget.LinearLayout[{i}]')
                if not item.exists:
                    break
                combined_text = self._get_listview_item_text(i)
                if not combined_text:
                    continue
                logging.debug(f"[Debug] Scan menu [{i}]: '{combined_text}'")
                if any(keyword in combined_text for keyword in switch_keywords):
                    logging.info(f"[Found] Menu switch account via scan ListView LinearLayout[{i}]")
                    return item
        except Exception as e:
            logging.debug(f"[Debug] Scan ListView switch account gagal: {e}")

        return None

    def click_switch_account_if_available(self):
        if not self.open_whatsapp_menu():
            return False

        time.sleep(1.5)
        switch_account_btn = self._find_switch_account_button()
        if not switch_account_btn:
            logging.info("[Info] Menu 'Switch account' / 'Beralih akun' / 'Alihkan akun' tidak ditemukan.")
            subprocess.run(["adb", "-s", str(self.device_id), "shell", "input", "keyevent", "4"], check=False)
            return False

        switch_account_btn.click()
        logging.info("[Found] Tombol Beralih Akun (Switch Account) diklik.")
        logging.info("[Waiting] Menunggu WhatsApp beralih akun (10 detik)...")
        time.sleep(10)
        return True

    def settings_whatsapp(self):
        try:
            if self.d(description="Anda").exists:
                self.d(description="Anda").click()
                logging.info("[Success] click setting success (description='Anda')")
                time.sleep(1)
                return

            if self.d(description="You").exists:
                self.d(description="You").click()
                logging.info("[Success] click setting success (description='You')")
                time.sleep(1)
                return

            overflow = self.d(resourceId=f"{self.packageName}:id/menuitem_overflow")
            if not overflow.exists:
                overflow = self.d.xpath(f'//*[@resource-id="{self.packageName}:id/menuitem_overflow"]')
            if overflow.exists:
                overflow.click()
                logging.info("[Success] overflow menu dibuka")
                time.sleep(1)
            else:
                logging.warning("[Failed] Overflow menu tidak ditemukan")
                return

            setting_indo = self.d(description="Pengaturan")
            setting_eng = self.d(description="Settings")
            text_indo = self.d(text="Pengaturan")
            text_eng = self.d(text="Settings")

            if setting_indo.exists:
                setting_indo.click()
                logging.info("[Success] click setting success (description='Pengaturan')")
                time.sleep(1)
            elif setting_eng.exists:
                setting_eng.click()
                logging.info("[Success] click setting success (description='Settings')")
                time.sleep(1)
            elif text_indo.exists:
                text_indo.click()
                logging.info("[Success] click setting success (text='Pengaturan')")
                time.sleep(1)
            elif text_eng.exists:
                text_eng.click()
                logging.info("[Success] click setting success (text='Settings')")
                time.sleep(1)
            else:
                logging.warning("[Failed] Settings tidak ditemukan di overflow menu")
        except Exception as e:
            logging.error(f"[Error] Terjadi kesalahan saat memilih settings: {e}")

    def menu_chats(self):
        try:
            logging.debug("[*] Mencari tombol 'Chats'...")

            def find_chat_button():
                for txt in ["Chat", "Chats", "Obrolan"]:
                    elem = self.d(text=txt)
                    if elem.exists:
                        return elem
                # Fallback ke textMatches case-insensitive
                elem_regex = self.d(textMatches="(?i)^(Chat|Chats|Obrolan)$")
                if elem_regex.exists:
                    return elem_regex
                return None

            check_menu_chat = find_chat_button()

            if not check_menu_chat:
                logging.info("[Info] Tombol 'Chats' tidak terlihat di atas, mencoba scroll ke bawah sedikit...")
                self.swipe_up()
                time.sleep(1)
                check_menu_chat = find_chat_button()

            if not check_menu_chat:
                logging.warning("[Error] Tombol menu 'Chat' atau 'Chats' tidak ditemukan meskipun sudah discroll.")
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

    def chat_backup_preference(self, account_suffix="_account1"):
        try:
            if self._click_chat_backup_entry():
                self.swipe_up()
                time.sleep(1)
                self.swipe_up()
                time.sleep(1)

                self.check_and_enable_encryption(account_suffix=account_suffix)
                time.sleep(1)
            else:
                logging.warning("[Failed] Gagal klik cadangkan chat, elemen tidak ditemukan")
        except Exception as e:
            logging.error(f"[Error] Gagal menjalankan chat_backup_preference: {e}")

    def _find_encryption_button(self):
        if self.d(resourceId=f"{self.packageName}:id/row_text", text="Cadangan terenkripsi end-to-end").exists:
            return self.d(resourceId=f"{self.packageName}:id/row_text", text="Cadangan terenkripsi end-to-end")
        if self.d(resourceId=f"{self.packageName}:id/row_text", text="End-to-end encrypted backup").exists:
            return self.d(resourceId=f"{self.packageName}:id/row_text", text="End-to-end encrypted backup")
        if self.d(resourceId=f"{self.packageName}:id/row_text", textMatches="(?i).*encrypted backup.*").exists:
            return self.d(resourceId=f"{self.packageName}:id/row_text", textMatches="(?i).*encrypted backup.*")
        if self.d(resourceId=f"{self.packageName}:id/row_text", textMatches="(?i).*cadangan terenkripsi.*").exists:
            return self.d(resourceId=f"{self.packageName}:id/row_text", textMatches="(?i).*cadangan terenkripsi.*")
        return None

    def _get_encryption_key_paths(self, account_suffix="_account1"):
        if hasattr(self, "extract_wa") and self.extract_wa:
            key_dir = self.extract_wa.key_dir
            key_path = self.extract_wa.output_file
        else:
            key_dir = account_key_dir(str(self.device_id), account_suffix)
            key_path = key_file(str(self.device_id), account_suffix)
        return key_dir, key_path

    def _validate_encryption_key_file(self, account_suffix="_account1"):
        key_dir, key_path = self._get_encryption_key_paths(account_suffix)

        logging.info(f"[Info] Mengecek folder encryption key: {key_dir}")
        if not os.path.isdir(key_dir):
            logging.warning(f"[Warning] Folder kunci tidak ditemukan: {key_dir}")
            return False, key_path

        logging.info(f"[Info] Mengecek file encryption key: {key_path}")
        if not os.path.isfile(key_path):
            logging.warning(f"[Warning] File kunci tidak ditemukan: {key_path}")
            return False, key_path

        try:
            with open(key_path, "r") as f:
                key_content = f.read().strip()
        except OSError as e:
            logging.warning(f"[Warning] Gagal membaca file kunci: {key_path} ({e})")
            return False, key_path

        if not key_content:
            logging.warning(f"[Warning] File kunci kosong: {key_path}")
            return False, key_path

        if len(key_content) not in (64, 131):
            logging.warning(f"[Warning] File kunci tidak valid (panjang {len(key_content)}): {key_path}")
            return False, key_path

        return True, key_path

    def _get_encryption_status(self):
        for _ in range(2):
            if self.d(resourceId=f"{self.packageName}:id/enc_backup_enabled_landing_disable_button").exists:
                return "Nyala"
            if self.d(resourceId=f"{self.packageName}:id/enable_info_turn_on_button").exists:
                return "Mati"

            for text_on in ("Nyala", "On"):
                if self.d(resourceId=f"{self.packageName}:id/row_subtext", text=text_on).exists:
                    return "Nyala"
            for text_off in ("Mati", "Off"):
                if self.d(resourceId=f"{self.packageName}:id/row_subtext", text=text_off).exists:
                    return "Mati"

            try:
                for i in range(self.d(resourceId=f"{self.packageName}:id/row_subtext").count):
                    text = self.d(resourceId=f"{self.packageName}:id/row_subtext")[i].info.get("text", "").strip().lower()
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

    def _is_on_chat_backup_screen(self):
        if self.d(resourceId=f"{self.packageName}:id/google_drive_backup_now_btn").exists:
            return True
        if self.d(resourceId=f"{self.packageName}:id/cancel_download").exists:
            return True
        return False

    def _wait_for_backup_now_button(self, timeout=90):
        backup_now_btn = self.d(resourceId=f"{self.packageName}:id/google_drive_backup_now_btn")
        logging.info(f"[Waiting] Menunggu tombol Backup Now muncul (maks {timeout} detik)...")

        deadline = time.time() + timeout
        attempt = 0
        while time.time() < deadline:
            if backup_now_btn.exists:
                logging.info("[Found] Tombol Backup Now sudah muncul.")
                return True

            done_button = self.d(resourceId=f"{self.packageName}:id/enable_done_create_button")
            if done_button.exists:
                done_button.click()
                time.sleep(2)
                continue

            attempt += 1
            if attempt % 5 == 0:
                self._navigate_back_to_chat_backup(max_attempts=4)

            time.sleep(2)

        logging.warning("[Warning] Tombol Backup Now tidak muncul setelah menunggu.")
        return False

    def _is_on_chats_settings_screen(self):
        return self.d(resourceId=f"{self.packageName}:id/chat_backup_preference").exists

    def _click_chat_backup_entry(self):
        if self._is_on_chat_backup_screen():
            logging.info("[Info] Sudah di halaman cadangan chat, lewati klik entri.")
            return True

        if not self._is_on_chats_settings_screen():
            return False

        chat_backup = self.d(resourceId=f"{self.packageName}:id/chat_backup_preference")
        if chat_backup.exists:
            chat_backup.click(timeout=2)
            time.sleep(1)
            logging.info("[Success] Berhasil klik cadangan chat via resourceId")
            return True

        chat_backup = self.d.xpath(f'//*[@resource-id="{self.packageName}:id/chat_backup_preference"]/android.widget.LinearLayout[1]')
        if chat_backup.exists:
            chat_backup.click(timeout=2)
            time.sleep(1)
            logging.info("[Success] Berhasil klik cadangan chat via xpath fallback")
            return True

        for txt in ["Cadangan chat", "Chat backup", "Cadangan obrolan"]:
            elem = self.d(resourceId=f"{self.packageName}:id/chat_backup_preference", textContains=txt)
            if elem.exists:
                elem.click(timeout=2)
                time.sleep(1)
                logging.info(f"[Success] Berhasil klik cadangan chat via text '{txt}'")
                return True

        return False

    def _navigate_to_chat_backup_settings(self):
        self._ensure_app_foreground()
        self.settings_whatsapp()
        time.sleep(1)
        self.menu_chats()
        time.sleep(2)
        for _ in range(2):
            self.swipe_up()
            time.sleep(1)
        return self._click_chat_backup_entry()

    def _reopen_chat_backup_screen(self):
        logging.info("[Info] Membuka ulang halaman cadangan chat dari awal...")
        self.back_to_main_whatsapp()
        time.sleep(1)
        if self._navigate_to_chat_backup_settings():
            time.sleep(2)
            if self._is_on_chat_backup_screen():
                return True
        logging.warning("[Warning] Gagal membuka entri cadangan chat.")
        return False

    def _navigate_back_to_chat_backup(self, max_attempts=12):
        if self._is_on_chat_backup_screen():
            logging.info("[Info] Sudah berada di halaman cadangan chat.")
            return True

        for attempt in range(max_attempts):
            if self._is_on_chat_backup_screen():
                logging.info("[Info] Kembali ke halaman cadangan chat.")
                return True

            done_button = self.d(resourceId=f"{self.packageName}:id/enable_done_create_button")
            if done_button.exists:
                done_button.click()
                time.sleep(1.5)
                continue

            disable_done = self.d(resourceId=f"{self.packageName}:id/disable_done_done_button")
            if disable_done.exists:
                disable_done.click()
                time.sleep(1.5)
                continue

            if self._is_on_chats_settings_screen():
                if self._click_chat_backup_entry():
                    time.sleep(1.5)
                    if self._is_on_chat_backup_screen():
                        logging.info("[Info] Halaman cadangan chat dibuka dari daftar Chats.")
                        return True

            subprocess.run(["adb", "-s", str(self.device_id), "shell", "input", "keyevent", "4"], check=False)
            time.sleep(1.5)

        logging.warning("[Warning] Tidak dapat kembali ke halaman cadangan chat via tombol Back.")
        return self._reopen_chat_backup_screen()

    def _ensure_chat_backup_screen(self):
        if self._is_on_chat_backup_screen():
            return True
        return self._navigate_back_to_chat_backup()

    def _press_backup_now(self):
        self._ensure_chat_backup_screen()

        if not self._wait_for_backup_now_button():
            logging.warning("[Warning] Tombol Backup Now tidak ditemukan, gagal memulai backup.")
            return False

        backup_now_btn = self.d(resourceId=f"{self.packageName}:id/google_drive_backup_now_btn")
        backup_now_btn.click()
        logging.info("[Success] Tombol Backup Now ditekan.")
        time.sleep(2)
        self.wait_for_cancel_download()
        return True

    def check_and_enable_encryption(self, account_suffix="_account1"):
        try:
            logging.info("[Info] Memulai pengecekan enkripsi end-to-end...")

            encryption_button = self._find_encryption_button()
            if not encryption_button:
                logging.warning("[Error] Tombol enkripsi end-to-end tidak ditemukan.")
                return

            logging.info("[Info] Membuka halaman enkripsi end-to-end...")
            encryption_button.click()
            time.sleep(2)

            status = self._get_encryption_status()
            if status is None:
                logging.warning("[Error] Tidak ditemukan status enkripsi 'Nyala', 'On', 'Mati', atau 'Off'")
                return

            logging.info(f"[Info] Status enkripsi end-to-end: {status}")

            if status in ["Nyala", "On"]:
                key_valid, key_path = self._validate_encryption_key_file(account_suffix)
                if key_valid:
                    logging.info(f"[Info] Enkripsi aktif dan file key valid: {key_path}")
                    self._press_backup_now()
                    return

                logging.warning("[Warning] File encryption key tidak ada/tidak valid. Menonaktifkan enkripsi untuk generate key baru...")
                if not self._disable_encryption(already_on_encryption_screen=True):
                    logging.error("[Error] Gagal menonaktifkan enkripsi. Proses dihentikan.")
                    return
                status = "Mati"

            if status in ["Mati", "Off"]:
                self._enable_encryption_and_backup(account_suffix)

        except Exception as e:
            logging.error(f"[Error] Terjadi kesalahan saat memeriksa enkripsi: {e}")

    def _enable_encryption_and_backup(self, account_suffix="_account1"):
        use_encryption_key_button = self.d(resourceId=f"{self.packageName}:id/enable_education_use_encryption_key_button")
        encryption_key_info_button = self.d(resourceId=f"{self.packageName}:id/encryption_key_info_bottom_button")
        encryption_key_confirm_button = self.d(resourceId=f"{self.packageName}:id/encryption_key_confirm_button_confirm")
        enable_done_create_button = self.d(resourceId=f"{self.packageName}:id/enable_done_create_button")

        logging.info("[Info] Mengaktifkan enkripsi end-to-end...")
        encryption_button = self._find_encryption_button()
        if encryption_button and encryption_button.exists:
            encryption_button.click()
            time.sleep(2)

        self.enable_encryption()
        time.sleep(1)

        more_options_button = self.d(resourceId=f"{self.packageName}:id/enable_info_more_options_button")
        if more_options_button.exists(timeout=5):
            more_options_button.click(timeout=3)
            logging.info("[Success] Berhasil klik enable_info_more_options_button")
            time.sleep(1)
        else:
            logging.warning("[Warning] enable_info_more_options_button tidak ditemukan.")

        if use_encryption_key_button.exists:
            use_encryption_key_button.click()
        else:
            alt_key_button = self.d.xpath(f'//*[@resource-id="{self.packageName}:id/enc_backup_more_options_encryption_key"]/android.widget.LinearLayout[1]')
            if alt_key_button.exists:
                alt_key_button.click()
            else:
                logging.warning("[Warning] Tombol penggunaan encryption key tidak ditemukan.")
                return

        logging.info("[Info] Menggunakan kunci enkripsi 64 digit.")
        time.sleep(2)
        encryption_key_info_button.click()
        logging.info("[Info] Membuat kunci 64 digit.")
        time.sleep(1)

        extracted_key = self.extract_wa.extract_whatsapp_keys()
        if not extracted_key:
            logging.error("[Error] Gagal mengekstrak kunci enkripsi dari layar WhatsApp.")
            return
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
        self._press_backup_now()

    def _disable_encryption(self, already_on_encryption_screen=False):
        try:
            disable_button = self.d(resourceId=f"{self.packageName}:id/enc_backup_enabled_landing_disable_button")
            if not disable_button.exists and not already_on_encryption_screen:
                encryption_button = self._find_encryption_button()
                if not encryption_button:
                    logging.warning("[Error] Tombol enkripsi tidak ditemukan.")
                    return False
                encryption_button.click()
                time.sleep(1)
                disable_button = self.d(resourceId=f"{self.packageName}:id/enc_backup_enabled_landing_disable_button")

            if not disable_button.exists:
                logging.warning("[Error] Tombol nonaktifkan enkripsi tidak ditemukan.")
                return False

            forgot_key_button = self.d(resourceId=f"{self.packageName}:id/enc_backup_encryption_key_input_forgot")
            confirm_disable_button = self.d(resourceId=f"{self.packageName}:id/confirm_disable_disable_button")
            disable_done_button = self.d(resourceId=f"{self.packageName}:id/disable_done_done_button")

            disable_button.click()
            time.sleep(1)
            forgot_key_button.click()
            time.sleep(1)
            confirm_disable_button.click()
            time.sleep(1)
            disable_done_button.click()
            time.sleep(2)

            for _ in range(15):
                status = self._get_encryption_status()
                if status in ["Mati", "Off"]:
                    logging.info("[Success] Enkripsi berhasil dinonaktifkan.")
                    return True
                time.sleep(2)

            logging.warning("[Warning] Timeout menunggu enkripsi dinonaktifkan.")
            return False
        except Exception as e:
            logging.error(f"[Error] Terjadi kesalahan saat menonaktifkan enkripsi: {e}")
            return False

    def _disable_and_regenerate_key(self, status_check_func=None, already_on_encryption_screen=False):
        """Legacy wrapper - nonaktifkan enkripsi lalu aktifkan kembali dengan key baru."""
        if not self._disable_encryption(already_on_encryption_screen=already_on_encryption_screen):
            return
        self._enable_encryption_and_backup()

    def enable_encryption(self):
        try:
            enable_encryption_button = self.d(resourceId=f"{self.packageName}:id/enable_info_turn_on_button")
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
            self.d(resourceId=f"{self.packageName}:id/cancel_download").wait(timeout=10.0)
            
            if self.d(resourceId=f"{self.packageName}:id/cancel_download").exists:
                logging.info("[Waiting] Sedang Proses Backup/Upload...")
                while self.d(resourceId=f"{self.packageName}:id/cancel_download").exists:
                    time.sleep(2)
                logging.info("[Success] Proses backup selesai!!")
            else:
                logging.info("[Info] Proses backup berlangsung sangat cepat atau sudah selesai.")
                time.sleep(5)

            # Pastikan tombol backup now kembali muncul (standby)
            while not self.d(resourceId=f"{self.packageName}:id/google_drive_backup_now_btn").exists:
                time.sleep(2)

            logging.info("[Found] Berhasil Backup, melanjutkan proses penarikan data...")
            time.sleep(3)
            self.extract_wa.pull_whatsapp_database()
            time.sleep(3)
            self.extract_wa.decrypt_whatsapp_db()

        except Exception as e:
            logging.error(f"[Error] Terjadi kesalahan saat menunggu elemen: {e}")

    def run_all_automation(self, account_suffix="_account1", skip_clear_apps=False):
        self.extract_wa = WhatsappTools(package_name=self.packageName, account_suffix=account_suffix)
        
        if not skip_clear_apps:
            self.open_recent_apps()
            time.sleep(2)
            
        self.backup_chat()
        time.sleep(1)
        self.chat_backup_preference(account_suffix=account_suffix)
        time.sleep(2)
        # Tidak ada open_recent_apps() di sini agar tidak langsung force close

    def back_to_main_whatsapp(self):
        logging.info(f"[INFO] Mencoba kembali ke beranda utama {self.packageName}...")
        self._ensure_app_foreground()
        
        max_attempts = 10
        for _ in range(max_attempts):
            # Cek apakah sudah di beranda utama dengan melihat menu titik tiga
            menu_button = self.d.xpath(f'//*[@resource-id="{self.packageName}:id/menuitem_overflow"]')
            if menu_button.exists:
                logging.info("[Found] Sudah berada di menu utama WhatsApp.")
                return True
            
            # Jika belum, tekan tombol Back bawaan sistem Android
            logging.info("[Action] Menekan tombol Back sistem...")
            back_button = self.d(resourceId="com.android.systemui:id/back")
            if back_button.exists:
                back_button.click()
            else:
                # Fallback menggunakan adb keyevent
                subprocess.run(["adb", "-s", str(self.device_id), "shell", "input", "keyevent", "4"], check=False)
            time.sleep(1.5)
            
        logging.warning("[Warning] Tidak dapat memastikan sudah kembali ke menu utama setelah 10 percobaan.")
        return False
        
    def run_multi_account_automation(self):
        # 0. Bersihkan semua recent apps di awal sekali untuk memori yang bersih
        logging.info("[INFO] Membersihkan aplikasi latar belakang sebelum memulai...")
        self.open_recent_apps()
        time.sleep(2)

        # --- BLOK WHATSAPP REGULER ---
        self.packageName = "com.whatsapp"
        if self.packageName in self.d.app_list():
            logging.info(f"[INFO] ====== MEMULAI EKSTRAKSI {self.packageName} ======")
            logging.info(f"[INFO] Memulai ekstraksi untuk {self.packageName} (Akun 1)...")
            self.run_all_automation(account_suffix="_account1", skip_clear_apps=True)
            
            # 1. Kembali ke beranda utama perlahan-lahan
            self.back_to_main_whatsapp()
            
            logging.info(f"[INFO] Mengecek apakah ada Akun 2 (Switch Account) di {self.packageName}...")
            time.sleep(1)

            if self.click_switch_account_if_available():
                logging.info(f"[INFO] Memulai ekstraksi untuk {self.packageName} (Akun 2)...")
                self.run_all_automation(account_suffix="_account2", skip_clear_apps=True)

                # 2. Kembali ke beranda utama lagi perlahan-lahan
                self.back_to_main_whatsapp()

                # 3. Beralih kembali ke Akun 1 agar tersamar (stealth mode)
                logging.info("[INFO] Mengembalikan WhatsApp ke Akun 1 (Stealth Mode)...")
                time.sleep(1)
                if not self.click_switch_account_if_available():
                    logging.warning("[Warning] Tombol kembali ke Akun 1 tidak ditemukan!")
            else:
                logging.info("[Info] Tidak ada akun kedua (Beralih akun) yang terdeteksi.")
    
            logging.info(f"[Info] Proses {self.packageName} selesai.")
        else:
            logging.info(f"[INFO] {self.packageName} tidak terinstal di perangkat ini.")

        # --- BLOK WHATSAPP BUSINESS ---
        self.packageName = "com.whatsapp.w4b"
        if self.packageName in self.d.app_list():
            logging.info(f"[INFO] ====== MEMULAI EKSTRAKSI {self.packageName} ======")
            logging.info(f"[INFO] Memulai ekstraksi untuk {self.packageName} (Akun Tunggal - Business)...")
            self.open_recent_apps()
            time.sleep(2)
            self._ensure_app_foreground()
            self.run_all_automation(account_suffix="_business", skip_clear_apps=True)
            
            logging.info(f"[Info] Proses {self.packageName} selesai.")
        else:
            logging.info(f"[INFO] {self.packageName} tidak terinstal di perangkat ini.")
            
        # 4. Bersihkan recent apps di akhir keseluruhan proses
        logging.info("[Info] Seluruh proses selesai. Membersihkan recent apps untuk menghilangkan jejak...")
        self.open_recent_apps()
        time.sleep(2)
            
        logging.info("[SUCCESS] SELURUH PROSES EKSTRAKSI WHATSAPP TELAH SELESAI!")

if __name__ == "__main__":
    wa_automation = WhatsAppAutomation()
    wa_automation.run_multi_account_automation()

#