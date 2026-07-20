import subprocess
import os


def check_adb():
    print("-" * 48)
    print("Copyright © 2024 4n6. All rights reserved")
    print("-" * 48)
    try:
        subprocess.run(["adb", "version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("Command is running...")
    except Exception:
        print("Please check the USB cable.")
        exit(1)


def run_adb_commands():
    try:
        # Run adb shell uiautomator dump command
        subprocess.run(
            ["adb", "shell", "uiautomator", "dump", "/sdcard/encryption_key.xml"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Ensure the local directory exists
        local_dir = "extractors/whatsapp_extractor/pull/"
        if not os.path.exists(local_dir):
            os.makedirs(local_dir)
            print(f"Created directory: {local_dir}")
        else:
            print(f"Directory already exists: {local_dir}")

        # Run adb pull command to pull the file from the device to the local machine
        subprocess.run(
            ["adb", "pull", "/sdcard/encryption_key.xml", local_dir],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        print(f"File successfully pulled to: {local_dir}")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred: {e.stderr.decode().strip()}")
        exit(1)


if __name__ == "__main__":
    check_adb()
    run_adb_commands()