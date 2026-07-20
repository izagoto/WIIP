from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_db
from app.models.case_management import Investigator
from app.models.audit import AuditLog

router = APIRouter()

class InvestigatorCreate(BaseModel):
    name: str
    email: str
    department: str = "Digital Forensics"
    
class InvestigatorResponse(InvestigatorCreate):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class AuditLogResponse(BaseModel):
    id: int
    action: str
    resource_path: str
    timestamp: datetime
    details: str | None
    
    class Config:
        from_attributes = True

@router.post("/", response_model=InvestigatorResponse, status_code=status.HTTP_201_CREATED)
def register_investigator(inv_in: InvestigatorCreate, db: Session = Depends(get_db)):
    db_inv = db.query(Investigator).filter(Investigator.email == inv_in.email).first()
    if db_inv:
        raise HTTPException(status_code=400, detail="Email already registered")
        
    new_inv = Investigator(name=inv_in.name, email=inv_in.email, department=inv_in.department)
    db.add(new_inv)
    db.commit()
    db.refresh(new_inv)
    return new_inv

@router.get("/", response_model=List[InvestigatorResponse])
def get_investigators(db: Session = Depends(get_db)):
    return db.query(Investigator).all()

@router.get("/{investigator_id}/audit-logs", response_model=List[AuditLogResponse])
def get_investigator_audit_logs(investigator_id: int, db: Session = Depends(get_db)):
    logs = db.query(AuditLog).filter(AuditLog.investigator_id == investigator_id).order_by(AuditLog.timestamp.desc()).limit(100).all()
    return logs
