import uiautomator2 as u2


class RecentAppsAutomation:
    def __init__(self):
        print("[INFO] Menghubungkan ke perangkat Android...")
        self.device = u2.connect()

    def click_recent_apps(self):
        xpath = 'com.android.systemui'

        print(f"[INFO] Mencari elemen: {xpath}")

        if self.device.xpath(xpath).exists:
            print("[SUCCESS] Elemen ditemukan.")

            self.device.xpath(xpath).click()

            print("[SUCCESS] Tombol Recent Apps berhasil diklik.")

        else:
            print("[ERROR] Elemen tidak ditemukan.")
            print("[INFO] Klik dibatalkan.")


if __name__ == "__main__":
    automation = RecentAppsAutomation()
    automation.click_recent_apps()