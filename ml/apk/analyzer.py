from pathlib import Path

from ml.apk.parser import ApkParseResult, parse_apk


def analyze_apk(path: Path) -> ApkParseResult:
    return parse_apk(path)
