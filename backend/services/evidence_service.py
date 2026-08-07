import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.core.exceptions import AppError, NotFoundError
from backend.models.case import Case
from backend.models.evidence import Evidence
from backend.modules.d6_operations.audit import log_activity
from backend.modules.d7_evidence.geospatial import list_geospatial_evidence
from backend.schemas.evidence import EvidenceCreateRequest, EvidenceUpdateRequest, GeospatialLocation, GeospatialResponse, VaultGroup, VaultResponse
from backend.services.custody_service import CustodyService


class EvidenceService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_evidence(
        self,
        *,
        case_id: uuid.UUID | None = None,
        category: str | None = None,
        location: str | None = None,
        page: int = 1,
        limit: int = 50,
    ) -> tuple[int, int, int, list[Evidence]]:
        query = select(Evidence)
        if case_id is not None:
            query = query.where(Evidence.case_id == case_id)
        if category is not None:
            query = query.where(Evidence.type == category)
        if location is not None:
            query = query.where(Evidence.storage_location.ilike(f"%{location}%"))

        count_query = select(func.count()).select_from(Evidence)
        if case_id is not None:
            count_query = count_query.where(Evidence.case_id == case_id)
        if category is not None:
            count_query = count_query.where(Evidence.type == category)
        if location is not None:
            count_query = count_query.where(Evidence.storage_location.ilike(f"%{location}%"))

        total = self.db.scalar(count_query) or 0
        items = list(
            self.db.scalars(
                query.order_by(Evidence.created_at.desc()).offset((page - 1) * limit).limit(limit)
            )
        )
        return total, page, limit, items

    def get_evidence(self, evidence_id: uuid.UUID) -> Evidence:
        evidence = self.db.get(Evidence, evidence_id)
        if not evidence:
            raise NotFoundError("Evidence not found")
        return evidence

    def create_evidence(
        self,
        payload: EvidenceCreateRequest,
        *,
        created_by: uuid.UUID,
        ip_address: str | None = None,
    ) -> Evidence:
        if not self.db.get(Case, payload.case_id):
            raise AppError("invalid_case", "Case not found", status_code=422)

        evidence = Evidence(
            case_id=payload.case_id,
            type=payload.type,
            brand=payload.brand,
            imei=payload.imei,
            serial_number=payload.serial_number,
            capacity=payload.capacity,
            condition_on_receipt=payload.condition_on_receipt,
            receipt_photo_url=payload.receipt_photo_url,
            location_latitude=payload.location_latitude,
            location_longitude=payload.location_longitude,
            storage_location=payload.storage_location,
        )
        self.db.add(evidence)
        self.db.flush()
        CustodyService(self.db).record_initial_custody(
            evidence.id,
            holder_id=created_by,
        )
        log_activity(
            self.db,
            user_id=created_by,
            action="evidence.create",
            entity_type="evidence",
            entity_id=evidence.id,
            details={"case_id": str(evidence.case_id), "type": evidence.type},
            ip_address=ip_address,
        )
        self.db.commit()
        self.db.refresh(evidence)
        return evidence

    def update_evidence(
        self,
        evidence_id: uuid.UUID,
        payload: EvidenceUpdateRequest,
        *,
        updated_by: uuid.UUID,
        ip_address: str | None = None,
    ) -> Evidence:
        evidence = self.get_evidence(evidence_id)
        changes: dict[str, object] = {}

        for field in (
            "type",
            "brand",
            "imei",
            "serial_number",
            "capacity",
            "condition_on_receipt",
            "receipt_photo_url",
            "location_latitude",
            "location_longitude",
            "storage_location",
        ):
            value = getattr(payload, field)
            if value is not None:
                setattr(evidence, field, value)
                changes[field] = str(value) if field in {"location_latitude", "location_longitude"} else value

        if changes:
            log_activity(
                self.db,
                user_id=updated_by,
                action="evidence.update",
                entity_type="evidence",
                entity_id=evidence.id,
                details=changes,
                ip_address=ip_address,
            )
        self.db.commit()
        self.db.refresh(evidence)
        return evidence

    def get_vault_registry(
        self,
        *,
        location: str | None = None,
        category: str | None = None,
    ) -> VaultResponse:
        query = select(Evidence).where(Evidence.storage_location.is_not(None))
        if location is not None:
            query = query.where(Evidence.storage_location.ilike(f"%{location}%"))
        if category is not None:
            query = query.where(Evidence.type == category)

        items = list(self.db.scalars(query.order_by(Evidence.storage_location, Evidence.type)))
        grouped: dict[tuple[str, str], list[Evidence]] = {}
        for item in items:
            key = (item.storage_location or "Unassigned", item.type)
            grouped.setdefault(key, []).append(item)

        groups = [
            VaultGroup(
                storage_location=storage_location,
                category=evidence_type,
                count=len(evidence_items),
                evidence_ids=[evidence.id for evidence in evidence_items],
            )
            for (storage_location, evidence_type), evidence_items in sorted(grouped.items())
        ]
        return VaultResponse(total=len(items), groups=groups)

    def get_geospatial(self, *, case_id: uuid.UUID | None = None) -> GeospatialResponse:
        items = list_geospatial_evidence(self.db, case_id=case_id)
        return GeospatialResponse(
            locations=[
                GeospatialLocation(
                    evidence_id=item.id,
                    latitude=item.location_latitude,
                    longitude=item.location_longitude,
                    acquired_at=item.created_at,
                    case_id=item.case_id,
                )
                for item in items
                if item.location_latitude is not None and item.location_longitude is not None
            ]
        )
