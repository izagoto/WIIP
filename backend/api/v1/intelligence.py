from fastapi import APIRouter

router = APIRouter(prefix="/intelligence", tags=["Intelligence"])


@router.get("/dashboard")
def intelligence_dashboard() -> dict[str, str]:
    return {"message": "Not implemented — Sprint 5"}
