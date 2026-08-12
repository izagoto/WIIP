import logging
import re
import subprocess

from backend.core.exceptions import AppError
from backend.modules.d7_evidence.adb_helper import ADBHelper

logger = logging.getLogger(__name__)


def _extract_imei_from_service_call(slot: int, adb_path: str) -> str:
    def run_method(method: int) -> str:
        command = [
            adb_path,
            "shell",
            "service",
            "call",
            "iphonesubinfo",
            str(method),
            "i32",
            str(slot),
            "s16",
            "com.android.shell",
        ]
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=15, check=False)
        except Exception as exc:
            logger.warning("IMEI probe failed for slot %s method %s: %s", slot, method, exc)
            return ""
        matches = re.findall(r"'(.*?)'", result.stdout)
        imei_raw = "".join(matches).replace(".", "").strip()
        return imei_raw

    imei = run_method(4)
    if not imei or "0000" in imei or imei.startswith("000"):
        imei = run_method(5)
    return imei


def probe_connected_device() -> dict:
    adb = ADBHelper()
    adb_path = adb.adb_path

    status = {
        "is_cable_connected": adb.check_usb_cable(),
        "is_adb_connected": False,
        "adb_available": True,
        "serial_number": None,
        "type": None,
        "brand": None,
        "imei_slot1": None,
        "imei_slot2": None,
        "model": None,
        "android_version": None,
        "security_patch": None,
        "device_id": None,
        "message": None,
    }

    try:
        subprocess.run([adb_path, "version"], capture_output=True, check=True, timeout=5)
    except (FileNotFoundError, subprocess.CalledProcessError):
        status["adb_available"] = False
        status["message"] = (
            "ADB not found. Install Android Platform Tools and set ADB_PATH in .env "
            "(e.g. /opt/homebrew/bin/adb)."
        )
        return status

    if not status["is_cable_connected"]:
        status["message"] = "USB cable not detected. Connect the phone via USB."
        return status

    status["is_adb_connected"] = adb.check_adb_connection()
    if not status["is_adb_connected"]:
        status["message"] = (
            "Phone detected via USB but ADB is not authorized. "
            "Enable USB debugging and accept the authorization prompt."
        )
        return status

    device_id = adb.detect_device()
    if not device_id:
        status["message"] = "ADB connected but no authorized device found."
        return status

    model_name = adb.get_property(device_id, "ro.product.model").strip()
    brand_name = adb.get_property(device_id, "ro.product.brand").strip()
    android_version = adb.get_property(device_id, "ro.build.version.release").strip()
    security_patch = adb.get_property(device_id, "ro.build.version.security_patch").strip()
    serial_number = adb.get_property(device_id, "ro.serialno").strip()
    display_name = adb.get_device_name(device_id).strip() or model_name

    brand_label = display_name
    if brand_name and brand_name.lower() not in display_name.lower():
        brand_label = f"{brand_name.title()} {display_name}".strip()

    imei_slot1 = _extract_imei_from_service_call(2, adb_path)
    imei_slot2 = _extract_imei_from_service_call(1, adb_path)

    status.update(
        {
            "device_id": device_id,
            "serial_number": serial_number or None,
            "type": "Smartphone",
            "brand": brand_label or None,
            "model": model_name or None,
            "android_version": android_version or None,
            "security_patch": security_patch or None,
            "imei_slot1": imei_slot1 or None,
            "imei_slot2": imei_slot2 or None,
            "message": "Device probed successfully. Review fields before registration.",
        }
    )
    return status


def get_device_connection_status() -> dict:
    adb = ADBHelper()
    is_cable_connected = adb.check_usb_cable()
    is_adb_connected = adb.check_adb_connection() if is_cable_connected else False
    serial_number = None
    if is_adb_connected:
        device_id = adb.detect_device()
        if device_id:
            serial_number = adb.get_property(device_id, "ro.serialno").strip() or None

    message = "No USB device detected."
    if is_cable_connected and not is_adb_connected:
        message = "USB connected. Waiting for ADB authorization."
    elif is_adb_connected:
        message = "Device ready for probing."

    return {
        "is_cable_connected": is_cable_connected,
        "is_adb_connected": is_adb_connected,
        "serial_number": serial_number,
        "message": message,
    }


def require_probed_device() -> dict:
    probe = probe_connected_device()
    if not probe.get("is_adb_connected"):
        raise AppError(
            "device_not_ready",
            probe.get("message") or "Connected device is not ready",
            status_code=422,
            details=probe,
        )
    return probe
