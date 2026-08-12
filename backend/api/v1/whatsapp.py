import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status

from backend.api.deps import CurrentUser, DbSession, get_client_ip, require_roles
from backend.modules.d6_operations.rbac import READ_ROLES, WRITE_ROLES
from backend.schemas.common import PaginatedResponse
from backend.schemas.whatsapp import (
    WhatsAppConversationResponse,
    WhatsAppImportRequest,
    WhatsAppImportResponse,
    WhatsAppMessageResponse,
    WhatsAppProfileSummaryResponse,
    WhatsAppSearchResponse,
)
from backend.services.whatsapp_service import WhatsAppService

router = APIRouter(prefix="/whatsapp", tags=["WhatsApp Intelligence"])

ReadUser = Annotated[object, Depends(require_roles(*READ_ROLES))]
WriteUser = Annotated[object, Depends(require_roles(*WRITE_ROLES))]


@router.post(
    "/import",
    response_model=WhatsAppImportResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def import_whatsapp(
    payload: WhatsAppImportRequest,
    request: Request,
    db: DbSession,
    user: CurrentUser,
    _auth: WriteUser,
) -> WhatsAppImportResponse:
    return WhatsAppService(db).start_import(
        payload,
        user_id=user.id,
        ip_address=get_client_ip(request),
    )


@router.get("/import/{import_id}", response_model=WhatsAppImportResponse)
def get_whatsapp_import(
    import_id: uuid.UUID,
    db: DbSession,
    _user: CurrentUser,
    _auth: ReadUser,
) -> WhatsAppImportResponse:
    return WhatsAppService(db).get_import(import_id)


@router.get("/search", response_model=WhatsAppSearchResponse)
def search_whatsapp_messages(
    db: DbSession,
    _user: CurrentUser,
    _auth: ReadUser,
    q: str = Query(min_length=1),
    contact: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    content_type: str | None = None,
    case_id: uuid.UUID | None = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, ge=1, le=100),
) -> WhatsAppSearchResponse:
    return WhatsAppService(db).search_messages(
        q=q,
        contact=contact,
        start_date=start_date,
        end_date=end_date,
        content_type=content_type,
        case_id=case_id,
        page=page,
        limit=limit,
    )


@router.get("/conversations", response_model=PaginatedResponse[WhatsAppConversationResponse])
def list_whatsapp_conversations(
    db: DbSession,
    _user: CurrentUser,
    _auth: ReadUser,
    case_id: uuid.UUID | None = None,
    contact: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    keyword: str | None = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, ge=1, le=100),
) -> PaginatedResponse[WhatsAppConversationResponse]:
    total, page, limit, items = WhatsAppService(db).list_conversations(
        case_id=case_id,
        contact=contact,
        start_date=start_date,
        end_date=end_date,
        keyword=keyword,
        page=page,
        limit=limit,
    )
    return PaginatedResponse(total=total, page=page, limit=limit, data=items)


@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=PaginatedResponse[WhatsAppMessageResponse],
)
def list_whatsapp_messages(
    conversation_id: uuid.UUID,
    db: DbSession,
    _user: CurrentUser,
    _auth: ReadUser,
    keyword: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, ge=1, le=100),
) -> PaginatedResponse[WhatsAppMessageResponse]:
    total, page, limit, items = WhatsAppService(db).list_messages(
        conversation_id,
        keyword=keyword,
        start_date=start_date,
        end_date=end_date,
        page=page,
        limit=limit,
    )
    return PaginatedResponse(total=total, page=page, limit=limit, data=items)


@router.get(
    "/profiles/{conversation_id}/summary",
    response_model=WhatsAppProfileSummaryResponse,
)
def get_whatsapp_profile_summary(
    conversation_id: uuid.UUID,
    db: DbSession,
    _user: CurrentUser,
    _auth: ReadUser,
) -> WhatsAppProfileSummaryResponse:
    return WhatsAppService(db).get_profile_summary(conversation_id)
