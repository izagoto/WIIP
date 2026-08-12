VAULT_CATEGORIES = ("mobile", "device", "document", "media")

_SMARTPHONE_MARKERS = ("smartphone", "hp", "android", "tablet", "iphone", "seluler", "mobile")
_DOCUMENT_MARKERS = ("dokumen", "document")
_MEDIA_MARKERS = ("media", "flashdisk", "usb", "harddisk")


def derive_category(evidence_type: str) -> str:
    normalized = evidence_type.strip().lower()
    if any(marker in normalized for marker in _SMARTPHONE_MARKERS):
        return "mobile"
    if any(marker in normalized for marker in _DOCUMENT_MARKERS):
        return "document"
    if any(marker in normalized for marker in _MEDIA_MARKERS):
        return "media"
    if normalized in VAULT_CATEGORIES:
        return normalized
    return "device"


def is_smartphone_type(evidence_type: str) -> bool:
    return derive_category(evidence_type) == "mobile"
