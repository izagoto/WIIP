import uuid
from datetime import UTC, datetime

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from backend.core.exceptions import AppError, ConflictError, NotFoundError
from backend.models.case import Case
from backend.models.evidence import Evidence
from backend.modules.d6_operations.audit import log_activity
from backend.modules.d6_operations.case_guards import ensure_case_open
from backend.modules.d7_evidence.categories import derive_category
from backend.modules.d7_evidence.device_probe import get_device_connection_status, probe_connected_device
from backend.modules.d7_evidence.geospatial import list_geospatial_evidence
from backend.modules.d7_evidence.registration_number import format_registration_number, wib_day_bounds_utc
from backend.modules.d7_evidence.validation import validate_evidence_fields
from backend.schemas.evidence import (
    DeviceProbeResponse,
    DeviceStatusResponse,
    EvidenceCreateRequest,
    EvidenceUpdateRequest,
    GeospatialLocation,
    GeospatialResponse,
    VaultGroup,
    VaultResponse,
)
from backend.services.custody_service import CustodyService


class EvidenceService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_device_status(self) -> DeviceStatusResponse:
        return DeviceStatusResponse.model_validate(get_device_connection_status())

    def probe_device(self) -> DeviceProbeResponse:
        return DeviceProbeResponse.model_validate(probe_connected_device())

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
            query = query.where(Evidence.category == category)
        if location is not None:
            query = query.where(Evidence.storage_location.ilike(f"%{location}%"))

        count_query = select(func.count()).select_from(Evidence)
        if case_id is not None:
            count_query = count_query.where(Evidence.case_id == case_id)
        if category is not None:
            count_query = count_query.where(Evidence.category == category)
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

    def _ensure_unique_imeis(
        self,
        imei_slot1: str | None,
        imei_slot2: str | None,
        *,
        exclude_id: uuid.UUID | None = None,
    ) -> None:
        for imei in {value for value in (imei_slot1, imei_slot2) if value}:
            query = select(Evidence.id).where(
                or_(Evidence.imei_slot1 == imei, Evidence.imei_slot2 == imei)
            )
            if exclude_id is not None:
                query = query.where(Evidence.id != exclude_id)
            existing = self.db.scalar(query.limit(1))
            if existing:
                raise ConflictError(f"IMEI {imei} is already registered to another evidence item")

    def _generate_registration_number(self, received_at: datetime) -> str:
        start_utc, end_utc = wib_day_bounds_utc(received_at)
        today_count = (
            self.db.scalar(
                select(func.count())
                .select_from(Evidence)
                .where(Evidence.received_at >= start_utc, Evidence.received_at < end_utc)
            )
            or 0
        )
        return format_registration_number(received_at, today_count + 1)

    def _ensure_unique_registration_number(
        self,
        registration_number: str,
        *,
        exclude_id: uuid.UUID | None = None,
    ) -> None:
        query = select(Evidence.id).where(Evidence.registration_number == registration_number)
        if exclude_id is not None:
            query = query.where(Evidence.id != exclude_id)
        if self.db.scalar(query.limit(1)):
            raise ConflictError("Evidence registration number already exists")

    def create_evidence(
        self,
        payload: EvidenceCreateRequest,
        *,
        created_by: uuid.UUID,
        ip_address: str | None = None,
    ) -> Evidence:
        case = self.db.get(Case, payload.case_id)
        if not case:
            raise AppError("invalid_case", "Case not found", status_code=422)
        ensure_case_open(case, action="register evidence")

        normalized_slot1, normalized_slot2 = validate_evidence_fields(
            evidence_type=payload.type,
            brand=payload.brand,
            imei_slot1=payload.imei_slot1,
            imei_slot2=payload.imei_slot2,
            serial_number=payload.serial_number,
            location_latitude=payload.location_latitude,
            location_longitude=payload.location_longitude,
        )
        self._ensure_unique_imeis(normalized_slot1, normalized_slot2)

        received_at = payload.received_at or datetime.now(UTC)
        registration_number = payload.registration_number or self._generate_registration_number(received_at)
        self._ensure_unique_registration_number(registration_number)

        evidence = Evidence(
            case_id=payload.case_id,
            registration_number=registration_number,
            received_at=received_at,
            type=payload.type,
            category=derive_category(payload.type),
            brand=payload.brand.strip() if payload.brand else None,
            imei_slot1=normalized_slot1,
            imei_slot2=normalized_slot2,
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
            details={
                "case_id": str(evidence.case_id),
                "type": evidence.type,
                "registration_number": evidence.registration_number,
            },
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
        case = self.db.get(Case, evidence.case_id)
        if case:
            ensure_case_open(case, action="update evidence")
        changes: dict[str, object] = {}

        for field in (
            "registration_number",
            "received_at",
            "type",
            "brand",
            "imei_slot1",
            "imei_slot2",
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

        if payload.type is not None:
            evidence.category = derive_category(evidence.type)

        normalized_slot1, normalized_slot2 = validate_evidence_fields(
            evidence_type=evidence.type,
            brand=evidence.brand,
            imei_slot1=evidence.imei_slot1,
            imei_slot2=evidence.imei_slot2,
            serial_number=evidence.serial_number,
            location_latitude=evidence.location_latitude,
            location_longitude=evidence.location_longitude,
        )
        evidence.imei_slot1 = normalized_slot1
        evidence.imei_slot2 = normalized_slot2
        if evidence.brand is not None:
            evidence.brand = evidence.brand.strip()
        if evidence.registration_number:
            self._ensure_unique_registration_number(evidence.registration_number, exclude_id=evidence.id)
        self._ensure_unique_imeis(normalized_slot1, normalized_slot2, exclude_id=evidence.id)

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
            query = query.where(Evidence.category == category)

        items = list(self.db.scalars(query.order_by(Evidence.storage_location, Evidence.category)))
        grouped: dict[tuple[str, str], list[Evidence]] = {}
        for item in items:
            key = (item.storage_location or "Unassigned", item.category)
            grouped.setdefault(key, []).append(item)

        groups = [
            VaultGroup(
                storage_location=storage_location,
                category=evidence_category,
                count=len(evidence_items),
                evidence_ids=[evidence.id for evidence in evidence_items],
            )
            for (storage_location, evidence_category), evidence_items in sorted(grouped.items())
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
                    acquired_at=item.received_at,
                    case_id=item.case_id,
                )
                for item in items
                if item.location_latitude is not None and item.location_longitude is not None
            ]
        )
