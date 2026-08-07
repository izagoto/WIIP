from pathlib import Path

from ml.apk.analyzer import analyze_apk


def analyze_apk_file(path: Path) -> dict:
    result = analyze_apk(path)
    return {
        "package_name": result.package_name,
        "version": result.version,
        "permissions": result.permissions,
        "components": result.components,
        "certificate": result.certificate,
        "threat_indicators": result.threat_indicators,
    }
