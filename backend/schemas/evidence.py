import uuid
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

CustodyAction = Literal["received", "transferred"]
TransferStatus = Literal["pending", "approved", "rejected"]


class EvidenceCreateRequest(BaseModel):
    case_id: uuid.UUID
    registration_number: str | None = Field(
        default=None,
        max_length=50,
        description="Optional. Auto-generated if omitted (e.g. BB-100826-0001).",
    )
    received_at: datetime | None = Field(
        default=None,
        description="Tanggal dan waktu barang bukti diterima. Defaults to now if omitted.",
    )
    type: str = Field(
        min_length=1,
        max_length=50,
        description="Jenis barang bukti, e.g. Smartphone, Laptop, Dokumen.",
    )
    brand: str | None = Field(default=None, max_length=255)
    imei_slot1: str | None = Field(default=None, max_length=25)
    imei_slot2: str | None = Field(default=None, max_length=25)
    serial_number: str | None = Field(default=None, max_length=100)
    capacity: str | None = Field(default=None, max_length=50)
    condition_on_receipt: str | None = None
    receipt_photo_url: str | None = Field(default=None, max_length=500)
    location_latitude: Decimal | None = None
    location_longitude: Decimal | None = None
    storage_location: str | None = Field(default=None, max_length=255)

    @field_validator("registration_number", mode="before")
    @classmethod
    def normalize_registration_number(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            return value
        normalized = value.strip()
        if not normalized:
            return None
        if len(normalized) < 3:
            raise ValueError("Registration number must be at least 3 characters")
        return normalized

    @field_validator("type", mode="before")
    @classmethod
    def normalize_type(cls, value: str) -> str:
        if not isinstance(value, str):
            return value
        normalized = value.strip()
        if not normalized:
            raise ValueError("Evidence type is required")
        return normalized


class EvidenceUpdateRequest(BaseModel):
    registration_number: str | None = Field(default=None, max_length=50)
    received_at: datetime | None = None
    type: str | None = Field(default=None, min_length=1, max_length=50)
    brand: str | None = Field(default=None, max_length=255)
    imei_slot1: str | None = Field(default=None, max_length=25)
    imei_slot2: str | None = Field(default=None, max_length=25)
    serial_number: str | None = Field(default=None, max_length=100)
    capacity: str | None = Field(default=None, max_length=50)
    condition_on_receipt: str | None = None
    receipt_photo_url: str | None = Field(default=None, max_length=500)
    location_latitude: Decimal | None = None
    location_longitude: Decimal | None = None
    storage_location: str | None = Field(default=None, max_length=255)

    @field_validator("registration_number", mode="before")
    @classmethod
    def normalize_registration_number(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            return value
        normalized = value.strip()
        if not normalized:
            return None
        if len(normalized) < 3:
            raise ValueError("Registration number must be at least 3 characters")
        return normalized

    @field_validator("type", mode="before")
    @classmethod
    def normalize_type(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            return value
        normalized = value.strip()
        if not normalized:
            raise ValueError("Evidence type cannot be empty")
        return normalized


class EvidenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    case_id: uuid.UUID
    registration_number: str
    received_at: datetime
    type: str
    category: str
    brand: str | None
    imei_slot1: str | None
    imei_slot2: str | None
    serial_number: str | None
    capacity: str | None
    condition_on_receipt: str | None
    receipt_photo_url: str | None
    location_latitude: Decimal | None
    location_longitude: Decimal | None
    storage_location: str | None
    sha256_hash: str | None
    created_at: datetime
    updated_at: datetime


class DeviceStatusResponse(BaseModel):
    is_cable_connected: bool
    is_adb_connected: bool
    serial_number: str | None = None
    message: str | None = None


class DeviceProbeResponse(BaseModel):
    is_cable_connected: bool
    is_adb_connected: bool
    adb_available: bool = True
    serial_number: str | None = None
    type: str | None = None
    brand: str | None = None
    imei_slot1: str | None = None
    imei_slot2: str | None = None
    model: str | None = None
    android_version: str | None = None
    security_patch: str | None = None
    device_id: str | None = None
    message: str | None = None


class CustodyHistoryEntry(BaseModel):
    id: uuid.UUID
    holder: str | None
    action: str
    from_user: str | None = None
    to_user: str | None = None
    timestamp: datetime
    notes: str | None
    verified: bool


class CustodyHistoryResponse(BaseModel):
    evidence_id: uuid.UUID
    current_holder: str | None
    custody_history: list[CustodyHistoryEntry]


class TransferRequest(BaseModel):
    from_user_id: uuid.UUID
    to_user_id: uuid.UUID
    notes: str | None = None


class TransferResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    evidence_id: uuid.UUID
    from_user_id: uuid.UUID
    to_user_id: uuid.UUID
    status: str
    approved_by: uuid.UUID | None
    approved_at: datetime | None
    notes: str | None
    created_at: datetime


class TransferApprovalRequest(BaseModel):
    approved: bool
    notes: str | None = None


class IntegrityHistoryEntry(BaseModel):
    hash: str
    verified_at: datetime
    verified_by: uuid.UUID


class IntegrityResponse(BaseModel):
    evidence_id: uuid.UUID
    sha256_hash: str | None
    verified: bool
    last_verified_at: datetime | None
    history: list[IntegrityHistoryEntry]


class VaultGroup(BaseModel):
    storage_location: str
    category: str
    count: int
    evidence_ids: list[uuid.UUID]


class VaultResponse(BaseModel):
    total: int
    groups: list[VaultGroup]


class GeospatialLocation(BaseModel):
    evidence_id: uuid.UUID
    latitude: Decimal
    longitude: Decimal
    acquired_at: datetime
    case_id: uuid.UUID


class GeospatialResponse(BaseModel):
    locations: list[GeospatialLocation]
