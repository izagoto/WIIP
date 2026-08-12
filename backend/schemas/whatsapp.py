from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

WhatsAppAccount = Literal["account_wa_1", "account_wa_2", "account_wa_business"]
ImportStatus = Literal["queued", "processing", "completed", "failed"]


class WhatsAppImportRequest(BaseModel):
    case_id: UUID
    device_id: str = Field(min_length=1, max_length=100)
    account: WhatsAppAccount = "account_wa_1"
    source_path: str | None = Field(default=None, max_length=500)

    @field_validator("device_id", mode="before")
    @classmethod
    def normalize_device_id(cls, value: str) -> str:
        if not isinstance(value, str):
            return value
        normalized = value.strip()
        if not normalized:
            raise ValueError("device_id is required")
        return normalized

    @field_validator("source_path", mode="before")
    @classmethod
    def normalize_source_path(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            return value
        normalized = value.strip()
        return normalized or None


class WhatsAppImportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    import_id: UUID
    status: ImportStatus
    case_id: UUID
    device_id: str
    account: str
    conversations_imported: int | None = None
    messages_imported: int | None = None
    error_message: str | None = None
    created_at: datetime
    completed_at: datetime | None = None


class WhatsAppConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    case_id: UUID
    contact: str | None = None
    message_count: int
    first_message_date: datetime | None = None
    last_message_date: datetime | None = None
    group_name: str | None = None
    wa_chat_jid: str | None = None


class WhatsAppMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    conversation_id: UUID
    timestamp: datetime
    sender: str
    receiver: str
    content: str
    content_type: str


class WhatsAppSearchHit(BaseModel):
    id: UUID
    conversation_id: UUID
    timestamp: datetime
    sender: str
    content: str
    snippet: str
    content_type: str | None = None


class WhatsAppSearchResponse(BaseModel):
    total: int
    query: str
    page: int = 1
    limit: int = 50
    data: list[WhatsAppSearchHit]


class DominantContactStat(BaseModel):
    contact: str
    message_count: int
    interaction_frequency: float


class ActiveGroupStat(BaseModel):
    group_name: str
    message_count: int
    member_count: int


class CommunicationPatterns(BaseModel):
    peak_hours: list[int]
    average_messages_per_day: float
    most_active_day: str | None = None


class WhatsAppProfileSummaryResponse(BaseModel):
    conversation_id: UUID
    dominant_contacts: list[DominantContactStat]
    active_groups: list[ActiveGroupStat]
    communication_patterns: CommunicationPatterns
