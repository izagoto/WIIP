from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models.evidence import Evidence


def list_geospatial_evidence(
    db: Session,
    *,
    case_id=None,
) -> list[Evidence]:
    query = select(Evidence).where(
        Evidence.location_latitude.is_not(None),
        Evidence.location_longitude.is_not(None),
    )
    if case_id is not None:
        query = query.where(Evidence.case_id == case_id)
    return list(db.scalars(query.order_by(Evidence.created_at.desc())))


def has_valid_coordinates(latitude: Decimal | None, longitude: Decimal | None) -> bool:
    if latitude is None or longitude is None:
        return False
    return Decimal("-90") <= latitude <= Decimal("90") and Decimal("-180") <= longitude <= Decimal("180")
