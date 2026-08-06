import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Evidence(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "evidence"

    case_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cases.id"), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    brand: Mapped[str | None] = mapped_column(String(100), nullable=True)
    imei: Mapped[str | None] = mapped_column(String(25), nullable=True)
    serial_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    capacity: Mapped[str | None] = mapped_column(String(50), nullable=True)
    condition_on_receipt: Mapped[str | None] = mapped_column(Text, nullable=True)
    receipt_photo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    location_latitude: Mapped[Decimal | None] = mapped_column(Numeric(10, 8), nullable=True)
    location_longitude: Mapped[Decimal | None] = mapped_column(Numeric(11, 8), nullable=True)
    storage_location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sha256_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
