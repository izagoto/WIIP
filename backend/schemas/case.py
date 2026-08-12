import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.schemas.common import ActivityItem

CasePriorityType = Literal["low", "medium", "high", "critical"]
CaseStatusType = Literal["open", "in_progress", "closed"]
TaskUrgencyType = Literal["low", "medium", "high"]
TaskStatusApiType = Literal["TODO", "IN_PROGRESS", "DONE"]
TaskStatusDbType = Literal["todo", "in_progress", "done"]


class CaseCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    reference_number: str | None = Field(
        default=None,
        max_length=50,
        description="Optional. Auto-generated from title if omitted (e.g. DPO-100826-0001).",
    )
    description: str | None = None
    priority: CasePriorityType = "medium"
    assigned_unit: str | None = Field(default=None, max_length=100)
    registered_at: datetime | None = None

    @field_validator("reference_number", mode="before")
    @classmethod
    def normalize_reference_number(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            return value
        normalized = value.strip()
        if not normalized:
            return None
        if len(normalized) < 3:
            raise ValueError("Reference number must be at least 3 characters")
        return normalized


class CaseUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    reference_number: str | None = Field(default=None, max_length=50)
    description: str | None = None
    priority: CasePriorityType | None = None
    assigned_unit: str | None = Field(default=None, max_length=100)
    assigned_investigator: uuid.UUID | None = None
    registered_at: datetime | None = None

    @field_validator("reference_number", mode="before")
    @classmethod
    def normalize_reference_number(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            return value
        normalized = value.strip()
        if not normalized:
            return None
        if len(normalized) < 3:
            raise ValueError("Reference number must be at least 3 characters")
        return normalized


class CaseStatusUpdateRequest(BaseModel):
    status: CaseStatusType


class CaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    reference_number: str
    description: str | None
    priority: str
    status: str
    assigned_unit: str | None
    assigned_investigator: uuid.UUID | None = None
    registered_at: datetime
    created_at: datetime
    updated_at: datetime


class TaskCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    due_date: datetime | None = None
    urgency: TaskUrgencyType | None = None
    checklist: list[str] | None = None


class TaskUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    assignee: uuid.UUID | None = None
    due_date: datetime | None = None
    urgency: TaskUrgencyType | None = None
    checklist: list[str] | None = None
    status: TaskStatusDbType | None = None


class TaskMoveRequest(BaseModel):
    status: TaskStatusApiType


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    case_id: uuid.UUID
    title: str
    description: str | None
    assignee: uuid.UUID | None = None
    due_date: datetime | None
    urgency: str | None
    checklist: list[str] | None
    status: str
    created_at: datetime
    updated_at: datetime


class KanbanTaskCard(BaseModel):
    id: uuid.UUID
    title: str
    assignee: str | None
    due_date: datetime | None
    urgency: str | None


class KanbanBoardResponse(BaseModel):
    columns: dict[str, list[KanbanTaskCard]]


class TaskSummary(BaseModel):
    total: int
    todo: int
    in_progress: int
    done: int
    overdue: int


class DashboardResponse(BaseModel):
    total_cases: int
    by_priority: dict[str, int]
    by_status: dict[str, int]
    task_load: dict[str, int]
    recent_activities: list[ActivityItem]


class CaseSummaryResponse(BaseModel):
    case_id: uuid.UUID
    reference_number: str
    title: str
    status: str
    priority: str
    registered_at: datetime
    task_summary: TaskSummary
    evidence_count: int
    whatsapp_conversation_count: int
    recent_activities: list[ActivityItem]
