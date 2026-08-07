import uuid
from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.core.exceptions import AppError, NotFoundError
from backend.models.intelligence import OrgHierarchy
from backend.models.user import User
from backend.modules.d6_operations.audit import log_activity
from backend.schemas.organization import (
    OrgHierarchyCreateRequest,
    OrgHierarchyNodeResponse,
    OrgHierarchyUpdateRequest,
)


class OrganizationService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_hierarchy_forest(self) -> list[OrgHierarchyNodeResponse]:
        nodes = list(self.db.scalars(select(OrgHierarchy).order_by(OrgHierarchy.created_at)).all())
        children_map: dict[uuid.UUID, list[OrgHierarchy]] = defaultdict(list)
        roots: list[OrgHierarchy] = []

        for node in nodes:
            if node.parent_id is None:
                roots.append(node)
            else:
                children_map[node.parent_id].append(node)

        return [self._to_tree(node, children_map) for node in roots]

    def create_node(
        self,
        payload: OrgHierarchyCreateRequest,
        *,
        created_by: uuid.UUID,
        ip_address: str | None = None,
    ) -> OrgHierarchy:
        self._ensure_user_exists(payload.user_id)
        if payload.parent_id is not None:
            self._get_node(payload.parent_id)

        node = OrgHierarchy(
            user_id=payload.user_id,
            name=payload.name,
            role=payload.role,
            parent_id=payload.parent_id,
        )
        self.db.add(node)
        self.db.flush()
        log_activity(
            self.db,
            user_id=created_by,
            action="org.create",
            entity_type="org_hierarchy",
            entity_id=node.id,
            details={"name": node.name},
            ip_address=ip_address,
        )
        self.db.commit()
        self.db.refresh(node)
        return node

    def update_node(
        self,
        node_id: uuid.UUID,
        payload: OrgHierarchyUpdateRequest,
        *,
        updated_by: uuid.UUID,
        ip_address: str | None = None,
    ) -> OrgHierarchy:
        node = self._get_node(node_id)
        changes: dict[str, object] = {}

        if payload.user_id is not None:
            self._ensure_user_exists(payload.user_id)
            node.user_id = payload.user_id
            changes["user_id"] = str(payload.user_id)

        if payload.name is not None:
            node.name = payload.name
            changes["name"] = payload.name

        if payload.role is not None:
            node.role = payload.role
            changes["role"] = payload.role

        if payload.parent_id is not None:
            if payload.parent_id == node.id:
                raise AppError("invalid_parent", "Node cannot be its own parent", status_code=422)
            self._get_node(payload.parent_id)
            node.parent_id = payload.parent_id
            changes["parent_id"] = str(payload.parent_id)

        if changes:
            log_activity(
                self.db,
                user_id=updated_by,
                action="org.update",
                entity_type="org_hierarchy",
                entity_id=node.id,
                details=changes,
                ip_address=ip_address,
            )
        self.db.commit()
        self.db.refresh(node)
        return node

    def _get_node(self, node_id: uuid.UUID) -> OrgHierarchy:
        node = self.db.get(OrgHierarchy, node_id)
        if not node:
            raise NotFoundError("Organization node not found")
        return node

    def _ensure_user_exists(self, user_id: uuid.UUID) -> None:
        if not self.db.get(User, user_id):
            raise AppError("invalid_user", "User not found", status_code=422)

    def _to_tree(
        self,
        node: OrgHierarchy,
        children_map: dict[uuid.UUID, list[OrgHierarchy]],
    ) -> OrgHierarchyNodeResponse:
        return OrgHierarchyNodeResponse(
            id=node.id,
            name=node.name,
            role=node.role,
            parent_id=node.parent_id,
            user_id=node.user_id,
            created_at=node.created_at,
            children=[self._to_tree(child, children_map) for child in children_map.get(node.id, [])],
        )
