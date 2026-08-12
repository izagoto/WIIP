import hashlib
import json

from backend.models.evidence import Evidence


def compute_evidence_hash(evidence: Evidence) -> str:
    payload = {
        "id": str(evidence.id),
        "case_id": str(evidence.case_id),
        "registration_number": evidence.registration_number,
        "received_at": evidence.received_at.isoformat() if evidence.received_at else None,
        "type": evidence.type,
        "category": evidence.category,
        "brand": evidence.brand,
        "imei_slot1": evidence.imei_slot1,
        "imei_slot2": evidence.imei_slot2,
        "serial_number": evidence.serial_number,
        "capacity": evidence.capacity,
        "condition_on_receipt": evidence.condition_on_receipt,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
