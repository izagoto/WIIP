import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Request, status

from backend.api.deps import CurrentUser, DbSession, get_client_ip, require_roles
from backend.modules.d6_operations.rbac import ADMIN_ROLES, READ_ROLES
from backend.schemas.organization import (
    OrgHierarchyCreateRequest,
    OrgHierarchyNodeResponse,
    OrgHierarchyUpdateRequest,
)
from backend.services.organization_service import OrganizationService

router = APIRouter(prefix="/organization", tags=["Organization"])

ReadUser = Annotated[object, Depends(require_roles(*READ_ROLES))]
AdminUser = Annotated[object, Depends(require_roles(*ADMIN_ROLES))]


@router.get("/hierarchy", response_model=list[OrgHierarchyNodeResponse])
def get_organization_hierarchy(
    db: DbSession,
    _user: CurrentUser,
    _auth: ReadUser,
) -> list[OrgHierarchyNodeResponse]:
    service = OrganizationService(db)
    return service.get_hierarchy_forest()


@router.post(
    "/hierarchy",
    response_model=OrgHierarchyNodeResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_organization_node(
    payload: OrgHierarchyCreateRequest,
    request: Request,
    db: DbSession,
    admin: CurrentUser,
    _auth: AdminUser,
) -> OrgHierarchyNodeResponse:
    service = OrganizationService(db)
    node = service.create_node(payload, created_by=admin.id, ip_address=get_client_ip(request))
    return OrgHierarchyNodeResponse(
        id=node.id,
        name=node.name,
        role=node.role,
        parent_id=node.parent_id,
        user_id=node.user_id,
        created_at=node.created_at,
        children=[],
    )


@router.patch("/hierarchy/{node_id}", response_model=OrgHierarchyNodeResponse)
def update_organization_node(
    node_id: uuid.UUID,
    payload: OrgHierarchyUpdateRequest,
    request: Request,
    db: DbSession,
    admin: CurrentUser,
    _auth: AdminUser,
) -> OrgHierarchyNodeResponse:
    service = OrganizationService(db)
    node = service.update_node(node_id, payload, updated_by=admin.id, ip_address=get_client_ip(request))
    return OrgHierarchyNodeResponse(
        id=node.id,
        name=node.name,
        role=node.role,
        parent_id=node.parent_id,
        user_id=node.user_id,
        created_at=node.created_at,
        children=[],
    )
