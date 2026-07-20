from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class EvidenceBase(BaseModel):
    source_type: str

class EvidenceResponse(EvidenceBase):
    id: int
    case_id: int
    file_path: str
    file_size: Optional[int] = None
    file_hash: str
    md5_hash: Optional[str] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
