from __future__ import annotations

import re
import zipfile
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path


@dataclass
class ApkParseResult:
    package_name: str | None = None
    version: str | None = None
    permissions: list[str] = field(default_factory=list)
    components: dict[str, list[str]] = field(default_factory=dict)
    certificate: dict | None = None
    threat_indicators: list[dict] = field(default_factory=list)


PERMISSION_PATTERN = re.compile(r"android\.permission\.[A-Z0-9_]+")
DANGEROUS_PERMISSIONS = {
    "android.permission.READ_SMS",
    "android.permission.SEND_SMS",
    "android.permission.READ_CONTACTS",
    "android.permission.ACCESS_FINE_LOCATION",
    "android.permission.CAMERA",
    "android.permission.RECORD_AUDIO",
    "android.permission.READ_CALL_LOG",
}


def _parse_with_androguard(path: Path) -> ApkParseResult | None:
    try:
        from androguard.core.apk import APK
    except ImportError:
        return None

    try:
        apk = APK(str(path))
    except Exception:
        return None

    try:
        permissions = sorted(apk.get_permissions() or [])
        components = {
            "activities": sorted(apk.get_activities() or []),
            "services": sorted(apk.get_services() or []),
            "receivers": sorted(apk.get_receivers() or []),
            "providers": sorted(apk.get_providers() or []),
        }
        cert = apk.get_certificate(apk.get_certificates()[0]) if apk.get_certificates() else None
        certificate = None
        if cert is not None:
            certificate = {
                "issuer": str(getattr(cert, "issuer", "unknown")),
                "valid_from": datetime.now(UTC).isoformat(),
                "valid_to": datetime.now(UTC).isoformat(),
            }

        return ApkParseResult(
            package_name=apk.get_package(),
            version=apk.get_androidversion_name(),
            permissions=permissions,
            components=components,
            certificate=certificate,
            threat_indicators=_build_threat_indicators(permissions, components),
        )
    except Exception:
        return None


def _build_threat_indicators(
    permissions: list[str],
    components: dict[str, list[str]],
) -> list[dict]:
    indicators: list[dict] = []
    for permission in permissions:
        if permission in DANGEROUS_PERMISSIONS:
            indicators.append(
                {
                    "type": "dangerous_permission",
                    "description": f"Application requests {permission}",
                    "severity": "high",
                }
            )
    if len(components.get("services", [])) > 5:
        indicators.append(
            {
                "type": "excessive_services",
                "description": "Application declares many background services",
                "severity": "medium",
            }
        )
    return indicators


def parse_apk_zip(path: Path) -> ApkParseResult:
    permissions: set[str] = set()
    components = {
        "activities": [],
        "services": [],
        "receivers": [],
        "providers": [],
    }
    package_name = path.stem

    with zipfile.ZipFile(path) as archive:
        for name in archive.namelist():
            if not name.endswith((".xml", ".dex", ".txt")):
                continue
            try:
                raw = archive.read(name)
            except KeyError:
                continue
            text = raw.decode("latin-1", errors="ignore")
            for permission in PERMISSION_PATTERN.findall(text):
                permissions.add(permission)
            lowered = name.lower()
            if "activity" in lowered:
                components["activities"].append(name)
            elif "service" in lowered:
                components["services"].append(name)
            elif "receiver" in lowered:
                components["receivers"].append(name)
            elif "provider" in lowered:
                components["providers"].append(name)

    return ApkParseResult(
        package_name=package_name,
        version="unknown",
        permissions=sorted(permissions),
        components=components,
        certificate={
            "issuer": "unknown",
            "valid_from": datetime.now(UTC).isoformat(),
            "valid_to": datetime.now(UTC).isoformat(),
        },
        threat_indicators=_build_threat_indicators(sorted(permissions), components),
    )


def parse_apk(path: Path) -> ApkParseResult:
    advanced = _parse_with_androguard(path)
    if advanced is not None:
        return advanced
    return parse_apk_zip(path)
