import logging
import platform
import subprocess
from typing import Optional

from backend.core.config import get_adb_path

logger = logging.getLogger(__name__)


class ADBHelper:
    adb_path: str

    def __init__(self, adb_path: str | None = None) -> None:
        self.adb_path = adb_path or get_adb_path()

    def run_command(self, command: str) -> str:
        try:
            full_command = [self.adb_path, *command.split()]
            result = subprocess.run(
                full_command,
                capture_output=True,
                text=True,
                check=False,
                timeout=15,
            )
            if result.returncode != 0:
                stderr = result.stderr.strip()
                if "No device found" in stderr:
                    logger.info("ADB command %s: no device found", command)
                else:
                    logger.warning(
                        "ADB command failed: %s stdout=%s stderr=%s",
                        command,
                        result.stdout.strip(),
                        stderr,
                    )
                return ""
            return result.stdout.strip()
        except FileNotFoundError:
            logger.error("ADB executable not found at %s", self.adb_path)
            return ""
        except subprocess.TimeoutExpired:
            logger.error("ADB command timed out: %s", command)
            return ""
        except Exception as exc:
            logger.error("Unexpected ADB error: %s", exc)
            return ""

    def detect_device(self) -> Optional[str]:
        result = self.run_command("devices")
        for line in result.splitlines()[1:]:
            if "\tdevice" in line:
                return line.split("\t")[0]
        return None

    def get_property(self, device_id: str, property_name: str) -> str:
        if not device_id:
            return ""
        return self.run_command(f"-s {device_id} shell getprop {property_name}")

    def check_usb_cable(self) -> bool:
        system = platform.system()
        if system == "Darwin":
            try:
                result = subprocess.run(
                    ["system_profiler", "SPUSBDataType"],
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=15,
                )
                return any("Product ID:" in line for line in result.stdout.splitlines())
            except Exception:
                return False
        if system == "Linux":
            try:
                result = subprocess.run(
                    ["lsusb"],
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=15,
                )
                device_lines = [
                    line
                    for line in result.stdout.splitlines()
                    if "Linux Foundation" not in line and "1d6b:" not in line
                ]
                return len(device_lines) > 0
            except Exception:
                return False
        return False

    def check_adb_connection(self) -> bool:
        state = self.run_command("get-state")
        return state == "device"

    def get_device_name(self, device_id: str) -> str:
        return self.run_command(f"-s {device_id} shell settings get global device_name")
