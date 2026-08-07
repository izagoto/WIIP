import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class OrgHierarchyNodeResponse(BaseModel):
    id: uuid.UUID
    name: str
    role: str | None = None
    parent_id: uuid.UUID | None = None
    user_id: uuid.UUID
    created_at: datetime
    children: list["OrgHierarchyNodeResponse"] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class OrgHierarchyCreateRequest(BaseModel):
    user_id: uuid.UUID
    name: str = Field(min_length=1, max_length=255)
    role: str | None = Field(default=None, max_length=50)
    parent_id: uuid.UUID | None = None


class OrgHierarchyUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    role: str | None = Field(default=None, max_length=50)
    parent_id: uuid.UUID | None = None
    user_id: uuid.UUID | None = None
