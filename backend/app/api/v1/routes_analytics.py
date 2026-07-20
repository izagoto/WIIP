from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.case_management import Case

from app.engines.correlation import CorrelationEngine
from app.engines.behavior import BehaviorEngine
from app.engines.graph import GraphEngine

router = APIRouter()

def verify_case(case_id: int, db: Session):
    db_case = db.query(Case).filter(Case.id == case_id).first()
    if not db_case:
        raise HTTPException(status_code=404, detail="Case not found")
    return db_case

@router.get("/cases/{case_id}/analytics/correlation/forwarded")
def trace_forwarded_message(case_id: int, text_snippet: str, db: Session = Depends(get_db)):
    """Traces a message by text snippet to see its forward chain."""
    verify_case(case_id, db)
    engine = CorrelationEngine(db, case_id)
    return {"trace": engine.trace_forwarded_messages(text_snippet)}

@router.get("/cases/{case_id}/analytics/correlation/common-groups")
def find_common_groups(case_id: int, person1: int, person2: int, db: Session = Depends(get_db)):
    """Finds groups where two individuals are both active."""
    verify_case(case_id, db)
    engine = CorrelationEngine(db, case_id)
    return {"common_groups": engine.find_common_groups(person1, person2)}

@router.get("/cases/{case_id}/analytics/behavior/bursts")
def detect_activity_bursts(case_id: int, db: Session = Depends(get_db)):
    """Detects sudden spikes in messaging activity (anomalies)."""
    verify_case(case_id, db)
    engine = BehaviorEngine(db, case_id)
    return {"bursts": engine.detect_activity_bursts()}

@router.get("/cases/{case_id}/analytics/behavior/active-hours")
def profile_active_hours(case_id: int, person_id: int, db: Session = Depends(get_db)):
    """Profiles the 24-hour active windows of a specific person."""
    verify_case(case_id, db)
    engine = BehaviorEngine(db, case_id)
    return {"active_hours": engine.profile_active_hours(person_id)}

@router.get("/cases/{case_id}/analytics/graph/centrality")
def get_graph_centrality(case_id: int, db: Session = Depends(get_db)):
    """Returns top influencers (degree centrality) and bridges (betweenness)."""
    verify_case(case_id, db)
    engine = GraphEngine(db, case_id)
    return engine.get_centrality_metrics()
