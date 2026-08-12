import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Evidence(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "evidence"

    case_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cases.id"), nullable=False, index=True)
    registration_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    category: Mapped[str] = mapped_column(String(20), nullable=False, default="mobile", index=True)
    brand: Mapped[str | None] = mapped_column(String(255), nullable=True)
    imei_slot1: Mapped[str | None] = mapped_column(String(25), nullable=True, index=True)
    imei_slot2: Mapped[str | None] = mapped_column(String(25), nullable=True, index=True)
    serial_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    capacity: Mapped[str | None] = mapped_column(String(50), nullable=True)
    condition_on_receipt: Mapped[str | None] = mapped_column(Text, nullable=True)
    receipt_photo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    location_latitude: Mapped[Decimal | None] = mapped_column(Numeric(10, 8), nullable=True)
    location_longitude: Mapped[Decimal | None] = mapped_column(Numeric(11, 8), nullable=True)
    storage_location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sha256_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
