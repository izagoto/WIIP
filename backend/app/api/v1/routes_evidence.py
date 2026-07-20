from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.case_management import Case, Investigator
from app.schemas.evidence import EvidenceResponse
from app.services.evidence_service import EvidenceService
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..')))
from worker.tasks.evidence_parser import parse_evidence_task

router = APIRouter()

@router.post("/cases/{case_id}/evidence", response_model=EvidenceResponse, status_code=status.HTTP_201_CREATED)
def upload_evidence(
    case_id: int,
    file: UploadFile = File(...),
    source_type: str = Form("whatsapp_db"),
    investigator_id: int = Form(...),
    db: Session = Depends(get_db)
):
    # Verify case exists
    db_case = db.query(Case).filter(Case.id == case_id).first()
    if not db_case:
        raise HTTPException(status_code=404, detail="Case not found")

    # Check if investigator exists
    investigator = db.query(Investigator).filter(Investigator.id == investigator_id).first()
    if not investigator:
        # Auto-create investigator for testing purposes if it doesn't exist
        investigator = Investigator(id=investigator_id, name=f"Investigator {investigator_id}", email=f"inv{investigator_id}@wiip.local")
        db.add(investigator)
        db.commit()
        db.refresh(investigator)

    service = EvidenceService(db)
    try:
        evidence = service.ingest_evidence(
            case_id=case_id,
            file=file,
            source_type=source_type,
            investigator_id=investigator_id
        )
        
        # Trigger Background Celery Task
        parse_evidence_task.delay(evidence.id)
        
        return evidence
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to ingest evidence: {str(e)}")

import tempfile
import subprocess
import shutil

@router.post("/cases/{case_id}/evidence/decrypt-upload", response_model=EvidenceResponse, status_code=status.HTTP_201_CREATED)
def decrypt_and_upload_evidence(
    case_id: int,
    db_file: UploadFile = File(...),
    key_file: UploadFile = File(...),
    investigator_id: int = Form(...),
    db: Session = Depends(get_db)
):
    """
    Uploads an encrypted WhatsApp database (.crypt14/15) along with its key.
    The server will decrypt it locally, convert to SDP, and start parsing.
    """
    # Verify case and investigator (Simplified for brevity, assumes they exist or auto-create)
    db_case = db.query(Case).filter(Case.id == case_id).first()
    if not db_case:
        raise HTTPException(status_code=404, detail="Case not found")

    investigator = db.query(Investigator).filter(Investigator.id == investigator_id).first()
    if not investigator:
        investigator = Investigator(id=investigator_id, name=f"Investigator {investigator_id}", email=f"inv{investigator_id}@wiip.local")
        db.add(investigator)
        db.commit()

    # Create temporary paths
    tmp_dir = tempfile.mkdtemp()
    tmp_db_path = os.path.join(tmp_dir, "msgstore.db.crypt14")
    tmp_key_path = os.path.join(tmp_dir, "key")
    tmp_out_path = os.path.join(tmp_dir, "msgstore.db")

    try:
        # Save uploaded files
        with open(tmp_db_path, "wb") as f_db:
            shutil.copyfileobj(db_file.file, f_db)
        with open(tmp_key_path, "wb") as f_key:
            shutil.copyfileobj(key_file.file, f_key)

        # Run the extractor script
        extractor_script = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'extractors', 'whatsapp_extractor', 'decrypt-wa.py'))
        
        result = subprocess.run(
            ["python", extractor_script, tmp_key_path, tmp_db_path, tmp_out_path],
            capture_output=True,
            text=True
        )

        if result.returncode != 0 or not os.path.exists(tmp_out_path):
            raise HTTPException(status_code=400, detail=f"Decryption failed: {result.stderr or result.stdout}")

        # Ingest the decrypted file
        service = EvidenceService(db)
        evidence = service.ingest_evidence(
            case_id=case_id,
            file=None, # type: ignore
            source_type="whatsapp_db",
            investigator_id=investigator_id,
            file_path_override=tmp_out_path,
            filename_override="msgstore.db"
        )
        
        # Start background task
        parse_evidence_task.delay(evidence.id)
        return evidence

    finally:
        # Cleanup temp directory
        if os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir)
