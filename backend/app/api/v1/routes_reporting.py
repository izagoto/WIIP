import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.case_management import Case
from app.services.report_generator import ReportGenerator

router = APIRouter()

def verify_case(case_id: int, db: Session):
    db_case = db.query(Case).filter(Case.id == case_id).first()
    if not db_case:
        raise HTTPException(status_code=404, detail="Case not found")
    return db_case

@router.get("/{case_id}/report/excel")
def download_excel_report(case_id: int, db: Session = Depends(get_db)):
    """
    Generates and downloads an Excel file containing all normalized messages.
    """
    verify_case(case_id, db)
    generator = ReportGenerator(db, case_id)
    file_path = generator.generate_excel()
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=500, detail="Failed to generate Excel report")
        
    return FileResponse(
        path=file_path,
        filename=f"WIIP_Case_{case_id}_Messages.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

@router.get("/{case_id}/report/pdf")
def download_pdf_report(case_id: int, db: Session = Depends(get_db)):
    """
    Generates and downloads a Court-Ready PDF summary report.
    """
    verify_case(case_id, db)
    generator = ReportGenerator(db, case_id)
    file_path = generator.generate_pdf()
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=500, detail="Failed to generate PDF report")
        
    return FileResponse(
        path=file_path,
        filename=f"WIIP_Case_{case_id}_Analytical_Report.pdf",
        media_type="application/pdf"
    )
