import uuid
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

EvidenceType = Literal["device", "mobile", "document", "media"]
CustodyAction = Literal["received", "transferred"]
TransferStatus = Literal["pending", "approved", "rejected"]


class EvidenceCreateRequest(BaseModel):
    case_id: uuid.UUID
    type: EvidenceType
    brand: str | None = Field(default=None, max_length=100)
    imei: str | None = Field(default=None, max_length=25)
    serial_number: str | None = Field(default=None, max_length=100)
    capacity: str | None = Field(default=None, max_length=50)
    condition_on_receipt: str | None = None
    receipt_photo_url: str | None = Field(default=None, max_length=500)
    location_latitude: Decimal | None = None
    location_longitude: Decimal | None = None
    storage_location: str | None = Field(default=None, max_length=255)


class EvidenceUpdateRequest(BaseModel):
    type: EvidenceType | None = None
    brand: str | None = Field(default=None, max_length=100)
    imei: str | None = Field(default=None, max_length=25)
    serial_number: str | None = Field(default=None, max_length=100)
    capacity: str | None = Field(default=None, max_length=50)
    condition_on_receipt: str | None = None
    receipt_photo_url: str | None = Field(default=None, max_length=500)
    location_latitude: Decimal | None = None
    location_longitude: Decimal | None = None
    storage_location: str | None = Field(default=None, max_length=255)


class EvidenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    case_id: uuid.UUID
    type: str
    brand: str | None
    imei: str | None
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
