from worker.celery_app import celery_app
from app.core.database import SessionLocal
from app.normalization.whatsapp_parser import WhatsAppParser
from app.models.case_management import Evidence

@celery_app.task(bind=True, name="parse_evidence_task")
def parse_evidence_task(self, evidence_id: int):
    """
    Celery background task to parse an uploaded WhatsApp DB.
    """
    db = SessionLocal()
    try:
        evidence = db.query(Evidence).filter(Evidence.id == evidence_id).first()
        if not evidence:
            return {"status": "error", "message": f"Evidence {evidence_id} not found."}
            
        # Update status to processing
        evidence.status = "processing" # type: ignore
        db.commit()
        
        # Start Parsing
        parser = WhatsAppParser(db_session=db, evidence_id=evidence_id)
        parser.parse()
        
        # Update status to processed
        evidence.status = "processed" # type: ignore
        db.commit()
        
        return {"status": "success", "message": f"Successfully parsed evidence {evidence_id}"}
        
    except Exception as e:
        db.rollback()
        # Mark as error
        evidence = db.query(Evidence).filter(Evidence.id == evidence_id).first()
        if evidence:
            evidence.status = "error" # type: ignore
            db.commit()
        raise e
    finally:
        db.close()
