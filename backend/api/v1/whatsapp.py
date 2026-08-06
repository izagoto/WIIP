from fastapi import APIRouter

router = APIRouter(prefix="/whatsapp", tags=["WhatsApp Intelligence"])


@router.post("/import")
def import_whatsapp() -> dict[str, str]:
    return {"message": "Not implemented — Sprint 1 follow-up"}
