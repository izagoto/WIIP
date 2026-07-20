import os
import io
import asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import UploadFile

from app.models.base import Base
from app.models.case_management import Case, Investigator
from app.services.evidence_service import EvidenceService
from app.core.config import settings

# Test DB Setup
engine = create_engine(settings.DATABASE_URL)
Base.metadata.create_all(bind=engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def test_ingestion():
    db = SessionLocal()
    
    # 1. Setup Mock Data (Investigator & Case)
    investigator = db.query(Investigator).first()
    if not investigator:
        investigator = Investigator(name="Test Investigator", email="test@wiip.local")
        db.add(investigator)
        db.commit()
        db.refresh(investigator)

    case = db.query(Case).first()
    if not case:
        case = Case(title="Test Case 1", investigator_id=investigator.id)
        db.add(case)
        db.commit()
        db.refresh(case)

    # 2. Create Dummy UploadFile
    dummy_content = b"This is a dummy evidence file content for hash testing."
    dummy_file = io.BytesIO(dummy_content)
    upload_file = UploadFile(filename="dummy_evidence.txt", file=dummy_file)

    # 3. Test Service
    print("Testing EvidenceService.ingest_evidence...")
    service = EvidenceService(db)
    
    try:
        evidence = service.ingest_evidence(
            case_id=int(case.id), # type: ignore
            file=upload_file,
            source_type="test_file",
            investigator_id=int(investigator.id) # type: ignore
        )
        
        print(f"Success! Evidence saved with ID: {evidence.id}")
        print(f"File Path: {evidence.file_path}")
        print(f"File Size: {evidence.file_size} bytes")
        print(f"SHA-256 Hash: {evidence.file_hash}")
        print(f"MD5 Hash: {evidence.md5_hash}")
        
        import typing
        # Verify Chain of Custody
        coc = typing.cast(list, evidence.chain_of_custody)
        print(f"Chain of custody events recorded: {len(coc)}")
        if len(coc) > 0:
            print(f"Latest Action: {coc[0].action}")
            print(f"Notes: {coc[0].notes}")
            
    except Exception as e:
        print(f"Error during ingestion: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_ingestion()
