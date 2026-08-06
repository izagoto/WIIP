import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base, UUIDPrimaryKeyMixin


class WhatsAppData(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "whatsapp_data"
    __table_args__ = (UniqueConstraint("case_id", "wa_chat_jid", name="uq_whatsapp_case_jid"),)

    case_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cases.id"), nullable=False, index=True)
    wa_chat_jid: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    contact: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    message_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    first_message_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_message_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    group_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    messages: Mapped[list["WhatsAppMessage"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
    )


class WhatsAppMessage(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "whatsapp_messages"

    conversation_record_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("whatsapp_data.id"),
        nullable=False,
        index=True,
    )
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    sender: Mapped[str] = mapped_column(String(255), nullable=False)
    receiver: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_type: Mapped[str] = mapped_column(String(20), nullable=False, default="text")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    conversation: Mapped[WhatsAppData] = relationship(back_populates="messages")


class WhatsAppImport(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "whatsapp_imports"

    case_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cases.id"), nullable=False)
    device_id: Mapped[str] = mapped_column(String(100), nullable=False)
    account: Mapped[str] = mapped_column(String(50), nullable=False)
    source_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="queued")
    conversations_imported: Mapped[int | None] = mapped_column(Integer, nullable=True)
    messages_imported: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    celery_task_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
