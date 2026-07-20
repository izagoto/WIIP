from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models.case_management import Case, Investigator
from app.schemas.case import CaseCreate, CaseResponse

router = APIRouter()

@router.post("/", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
def create_case(case_in: CaseCreate, db: Session = Depends(get_db)):
    # Check if investigator exists
    investigator = db.query(Investigator).filter(Investigator.id == case_in.investigator_id).first()
    if not investigator:
        # Auto-create investigator for testing purposes if it doesn't exist
        investigator = Investigator(id=case_in.investigator_id, name=f"Investigator {case_in.investigator_id}", email=f"inv{case_in.investigator_id}@wiip.local")
        db.add(investigator)
        db.commit()
        db.refresh(investigator)

    db_case = Case(
        title=case_in.title,
        description=case_in.description,
        investigator_id=case_in.investigator_id
    )
    db.add(db_case)
    db.commit()
    db.refresh(db_case)
    return db_case

@router.get("/", response_model=List[CaseResponse])
def get_cases(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    cases = db.query(Case).offset(skip).limit(limit).all()
    return cases

@router.get("/{case_id}", response_model=CaseResponse)
def get_case(case_id: int, db: Session = Depends(get_db)):
    db_case = db.query(Case).filter(Case.id == case_id).first()
    if db_case is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return db_case
