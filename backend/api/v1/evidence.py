import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status
from fastapi.responses import Response

from backend.api.deps import CurrentUser, DbSession, get_client_ip, require_roles
from backend.modules.d6_operations.rbac import READ_ROLES, WRITE_ROLES
from backend.schemas.common import PaginatedResponse
from backend.schemas.evidence import (
    CustodyHistoryResponse,
    DeviceProbeResponse,
    DeviceStatusResponse,
    EvidenceCreateRequest,
    EvidenceResponse,
    EvidenceUpdateRequest,
    GeospatialResponse,
    IntegrityResponse,
    TransferApprovalRequest,
    TransferRequest,
    TransferResponse,
    VaultResponse,
)
from backend.services.custody_service import CustodyService
from backend.services.evidence_service import EvidenceService
from backend.services.report_service import ReportService

router = APIRouter(prefix="/evidence", tags=["Evidence"])

ReadUser = Annotated[object, Depends(require_roles(*READ_ROLES))]
WriteUser = Annotated[object, Depends(require_roles(*WRITE_ROLES))]


def _evidence_response(evidence) -> EvidenceResponse:
    return EvidenceResponse.model_validate(evidence)


@router.get("/device-status", response_model=DeviceStatusResponse)
def get_device_status(
    _user: CurrentUser,
    _auth: ReadUser,
    db: DbSession,
) -> DeviceStatusResponse:
    return EvidenceService(db).get_device_status()


@router.get("/device-probe", response_model=DeviceProbeResponse)
def probe_connected_device(
    _user: CurrentUser,
    _auth: WriteUser,
    db: DbSession,
) -> DeviceProbeResponse:
    return EvidenceService(db).probe_device()


@router.get("/vault", response_model=VaultResponse)
def get_vault_registry(
    db: DbSession,
    _user: CurrentUser,
    _auth: ReadUser,
    location: str | None = None,
    category: str | None = None,
) -> VaultResponse:
    return EvidenceService(db).get_vault_registry(location=location, category=category)


@router.get("/geospatial", response_model=GeospatialResponse)
def get_geospatial_evidence(
    db: DbSession,
    _user: CurrentUser,
    _auth: ReadUser,
    case_id: uuid.UUID | None = None,
) -> GeospatialResponse:
    return EvidenceService(db).get_geospatial(case_id=case_id)


@router.patch("/transfers/{transfer_id}/approve", response_model=TransferResponse)
def approve_transfer(
    transfer_id: uuid.UUID,
    payload: TransferApprovalRequest,
    request: Request,
    db: DbSession,
    user: CurrentUser,
    _auth: WriteUser,
) -> TransferResponse:
    return CustodyService(db).approve_transfer(
        transfer_id,
        payload,
        approver_id=user.id,
        ip_address=get_client_ip(request),
    )


@router.get("", response_model=PaginatedResponse[EvidenceResponse])
def list_evidence(
    db: DbSession,
    _user: CurrentUser,
    _auth: ReadUser,
    case_id: uuid.UUID | None = None,
    category: str | None = None,
    location: str | None = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, ge=1, le=100),
) -> PaginatedResponse[EvidenceResponse]:
    service = EvidenceService(db)
    total, page, limit, items = service.list_evidence(
        case_id=case_id,
        category=category,
        location=location,
        page=page,
        limit=limit,
    )
    return PaginatedResponse(
        total=total,
        page=page,
        limit=limit,
        data=[_evidence_response(item) for item in items],
    )


@router.post("", response_model=EvidenceResponse, status_code=status.HTTP_201_CREATED)
def create_evidence(
    payload: EvidenceCreateRequest,
    request: Request,
    db: DbSession,
    user: CurrentUser,
    _auth: WriteUser,
) -> EvidenceResponse:
    service = EvidenceService(db)
    evidence = service.create_evidence(
        payload,
        created_by=user.id,
        ip_address=get_client_ip(request),
    )
    return _evidence_response(evidence)


@router.get("/{evidence_id}/custody", response_model=CustodyHistoryResponse)
def get_custody_history(
    evidence_id: uuid.UUID,
    db: DbSession,
    _user: CurrentUser,
    _auth: ReadUser,
) -> CustodyHistoryResponse:
    return CustodyService(db).get_custody_history(evidence_id)


@router.post("/{evidence_id}/transfer", response_model=TransferResponse, status_code=status.HTTP_201_CREATED)
def request_transfer(
    evidence_id: uuid.UUID,
    payload: TransferRequest,
    request: Request,
    db: DbSession,
    user: CurrentUser,
    _auth: WriteUser,
) -> TransferResponse:
    return CustodyService(db).request_transfer(
        evidence_id,
        payload,
        requested_by=user.id,
        ip_address=get_client_ip(request),
    )


@router.get("/{evidence_id}/integrity", response_model=IntegrityResponse)
def get_integrity(
    evidence_id: uuid.UUID,
    db: DbSession,
    _user: CurrentUser,
    _auth: ReadUser,
) -> IntegrityResponse:
    return CustodyService(db).get_integrity(evidence_id)


@router.post("/{evidence_id}/verify-integrity", response_model=IntegrityResponse)
def verify_integrity(
    evidence_id: uuid.UUID,
    request: Request,
    db: DbSession,
    user: CurrentUser,
    _auth: WriteUser,
) -> IntegrityResponse:
    return CustodyService(db).verify_integrity(
        evidence_id,
        verified_by=user.id,
        ip_address=get_client_ip(request),
    )


@router.get("/{evidence_id}/custody-report")
def get_custody_report(
    evidence_id: uuid.UUID,
    db: DbSession,
    _user: CurrentUser,
    _auth: ReadUser,
    evidence_ids: list[uuid.UUID] | None = Query(default=None),
) -> Response:
    ids = evidence_ids if evidence_ids else [evidence_id]
    if evidence_id not in ids:
        ids = [evidence_id, *ids]
    pdf_bytes = ReportService(db).generate_custody_report_pdf(ids)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="bast-{evidence_id}.pdf"'},
    )


@router.get("/{evidence_id}", response_model=EvidenceResponse)
def get_evidence(
    evidence_id: uuid.UUID,
    db: DbSession,
    _user: CurrentUser,
    _auth: ReadUser,
) -> EvidenceResponse:
    service = EvidenceService(db)
    return _evidence_response(service.get_evidence(evidence_id))


@router.patch("/{evidence_id}", response_model=EvidenceResponse)
def update_evidence(
    evidence_id: uuid.UUID,
    payload: EvidenceUpdateRequest,
    request: Request,
    db: DbSession,
    user: CurrentUser,
    _auth: WriteUser,
) -> EvidenceResponse:
    service = EvidenceService(db)
    evidence = service.update_evidence(
        evidence_id,
        payload,
        updated_by=user.id,
        ip_address=get_client_ip(request),
    )
    return _evidence_response(evidence)
