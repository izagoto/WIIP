import hashlib
import json

from backend.models.evidence import Evidence


def compute_evidence_hash(evidence: Evidence) -> str:
    payload = {
        "id": str(evidence.id),
        "case_id": str(evidence.case_id),
        "type": evidence.type,
        "brand": evidence.brand,
        "imei": evidence.imei,
        "serial_number": evidence.serial_number,
        "capacity": evidence.capacity,
        "condition_on_receipt": evidence.condition_on_receipt,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
