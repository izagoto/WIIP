import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.core.exceptions import AppError, NotFoundError
from backend.models.audit_log import AuditLog
from backend.models.case import Case, CasePriority, CaseStatus
from backend.models.evidence import Evidence
from backend.models.task import Task, TaskStatus
from backend.models.user import User
from backend.models.whatsapp import WhatsAppData
from backend.modules.d6_operations.audit import log_activity
from backend.modules.d6_operations.kanban import (
    KANBAN_COLUMNS,
    api_status_to_db,
    db_status_to_api,
)
from backend.schemas.case import (
    CaseCreateRequest,
    CaseSummaryResponse,
    CaseUpdateRequest,
    DashboardResponse,
    KanbanBoardResponse,
    KanbanTaskCard,
    TaskCreateRequest,
    TaskSummary,
    TaskUpdateRequest,
)
from backend.schemas.common import ActivityItem


class CaseService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_case(
        self,
        payload: CaseCreateRequest,
        *,
        created_by: uuid.UUID,
        ip_address: str | None = None,
    ) -> Case:
        if payload.assigned_investigator and not self._user_exists(payload.assigned_investigator):
            raise AppError("invalid_assignee", "Assigned investigator not found", status_code=422)

        case = Case(
            title=payload.title,
            description=payload.description,
            priority=payload.priority,
            assigned_unit=payload.assigned_unit,
            assigned_to=payload.assigned_investigator,
            created_by=created_by,
            status=CaseStatus.OPEN.value,
        )
        self.db.add(case)
        self.db.flush()
        log_activity(
            self.db,
            user_id=created_by,
            action="case.create",
            entity_type="case",
            entity_id=case.id,
            details={"title": case.title, "priority": case.priority},
            ip_address=ip_address,
        )
        self.db.commit()
        self.db.refresh(case)
        return case

    def list_cases(
        self,
        *,
        status: str | None = None,
        priority: str | None = None,
        assigned_to: uuid.UUID | None = None,
        page: int = 1,
        limit: int = 50,
    ) -> tuple[int, int, int, list[Case]]:
        query = select(Case)
        if status:
            query = query.where(Case.status == status)
        if priority:
            query = query.where(Case.priority == priority)
        if assigned_to:
            query = query.where(Case.assigned_to == assigned_to)

        count_query = select(func.count()).select_from(Case)
        if status:
            count_query = count_query.where(Case.status == status)
        if priority:
            count_query = count_query.where(Case.priority == priority)
        if assigned_to:
            count_query = count_query.where(Case.assigned_to == assigned_to)
        total = self.db.scalar(count_query) or 0
        cases = self.db.scalars(
            query.order_by(Case.created_at.desc()).offset((page - 1) * limit).limit(limit)
        ).all()
        return total, page, limit, list(cases)

    def get_case(self, case_id: uuid.UUID) -> Case:
        case = self.db.get(Case, case_id)
        if not case:
            raise NotFoundError("Case not found")
        return case

    def update_case(
        self,
        case_id: uuid.UUID,
        payload: CaseUpdateRequest,
        *,
        user_id: uuid.UUID,
        ip_address: str | None = None,
    ) -> Case:
        case = self.get_case(case_id)
        updates = payload.model_dump(exclude_unset=True)
        if "assigned_investigator" in updates:
            assignee = updates.pop("assigned_investigator")
            if assignee and not self._user_exists(assignee):
                raise AppError("invalid_assignee", "Assigned investigator not found", status_code=422)
            case.assigned_to = assignee

        for field, value in updates.items():
            setattr(case, field, value)

        log_activity(
            self.db,
            user_id=user_id,
            action="case.update",
            entity_type="case",
            entity_id=case.id,
            details=updates,
            ip_address=ip_address,
        )
        self.db.commit()
        self.db.refresh(case)
        return case

    def update_case_status(
        self,
        case_id: uuid.UUID,
        status: str,
        *,
        user_id: uuid.UUID,
        ip_address: str | None = None,
    ) -> Case:
        case = self.get_case(case_id)
        case.status = status
        log_activity(
            self.db,
            user_id=user_id,
            action="case.status_update",
            entity_type="case",
            entity_id=case.id,
            details={"status": status},
            ip_address=ip_address,
        )
        self.db.commit()
        self.db.refresh(case)
        return case

    def get_case_summary(self, case_id: uuid.UUID) -> CaseSummaryResponse:
        case = self.get_case(case_id)
        tasks = self.db.scalars(select(Task).where(Task.case_id == case_id)).all()
        now = datetime.now(UTC)

        task_summary = TaskSummary(
            total=len(tasks),
            todo=sum(1 for task in tasks if task.status == TaskStatus.TODO.value),
            in_progress=sum(1 for task in tasks if task.status == TaskStatus.IN_PROGRESS.value),
            done=sum(1 for task in tasks if task.status == TaskStatus.DONE.value),
            overdue=sum(
                1
                for task in tasks
                if task.due_date
                and task.due_date < now
                and task.status != TaskStatus.DONE.value
            ),
        )
        evidence_count = self.db.scalar(
            select(func.count()).select_from(Evidence).where(Evidence.case_id == case_id)
        ) or 0
        whatsapp_count = self.db.scalar(
            select(func.count()).select_from(WhatsAppData).where(WhatsAppData.case_id == case_id)
        ) or 0

        return CaseSummaryResponse(
            case_id=case.id,
            title=case.title,
            status=case.status,
            priority=case.priority,
            task_summary=task_summary,
            evidence_count=evidence_count,
            whatsapp_conversation_count=whatsapp_count,
            recent_activities=self._recent_activities(entity_type="case", entity_id=case_id),
        )

    def get_dashboard(self) -> DashboardResponse:
        cases = self.db.scalars(select(Case)).all()
        tasks = self.db.scalars(select(Task)).all()
        now = datetime.now(UTC)

        by_priority = {priority.value: 0 for priority in CasePriority}
        by_status = {status.value: 0 for status in CaseStatus}
        for case in cases:
            by_priority[case.priority] = by_priority.get(case.priority, 0) + 1
            by_status[case.status] = by_status.get(case.status, 0) + 1

        task_load = {
            "total_tasks": len(tasks),
            "completed": sum(1 for task in tasks if task.status == TaskStatus.DONE.value),
            "overdue": sum(
                1
                for task in tasks
                if task.due_date
                and task.due_date < now
                and task.status != TaskStatus.DONE.value
            ),
        }

        return DashboardResponse(
            total_cases=len(cases),
            by_priority=by_priority,
            by_status=by_status,
            task_load=task_load,
            recent_activities=self._recent_activities(),
        )

    def list_case_tasks(self, case_id: uuid.UUID) -> list[Task]:
        self.get_case(case_id)
        return list(self.db.scalars(select(Task).where(Task.case_id == case_id).order_by(Task.created_at.desc())))

    def create_task(
        self,
        case_id: uuid.UUID,
        payload: TaskCreateRequest,
        *,
        user_id: uuid.UUID,
        ip_address: str | None = None,
    ) -> Task:
        self.get_case(case_id)
        if payload.assignee and not self._user_exists(payload.assignee):
            raise AppError("invalid_assignee", "Assignee not found", status_code=422)

        task = Task(
            case_id=case_id,
            title=payload.title,
            description=payload.description,
            assignee_id=payload.assignee,
            due_date=payload.due_date,
            urgency=payload.urgency,
            checklist=payload.checklist,
            status=TaskStatus.TODO.value,
        )
        self.db.add(task)
        self.db.flush()
        log_activity(
            self.db,
            user_id=user_id,
            action="task.create",
            entity_type="task",
            entity_id=task.id,
            details={"case_id": str(case_id), "title": task.title},
            ip_address=ip_address,
        )
        self.db.commit()
        self.db.refresh(task)
        return task

    def get_task(self, task_id: uuid.UUID) -> Task:
        task = self.db.get(Task, task_id)
        if not task:
            raise NotFoundError("Task not found")
        return task

    def update_task(
        self,
        task_id: uuid.UUID,
        payload: TaskUpdateRequest,
        *,
        user_id: uuid.UUID,
        ip_address: str | None = None,
    ) -> Task:
        task = self.get_task(task_id)
        updates = payload.model_dump(exclude_unset=True)
        if "assignee" in updates:
            assignee = updates.pop("assignee")
            if assignee and not self._user_exists(assignee):
                raise AppError("invalid_assignee", "Assignee not found", status_code=422)
            task.assignee_id = assignee

        for field, value in updates.items():
            setattr(task, field, value)

        log_activity(
            self.db,
            user_id=user_id,
            action="task.update",
            entity_type="task",
            entity_id=task.id,
            details=updates,
            ip_address=ip_address,
        )
        self.db.commit()
        self.db.refresh(task)
        return task

    def move_task(
        self,
        task_id: uuid.UUID,
        api_status: str,
        *,
        user_id: uuid.UUID,
        ip_address: str | None = None,
    ) -> Task:
        task = self.get_task(task_id)
        try:
            task.status = api_status_to_db(api_status)
        except ValueError as exc:
            raise AppError("invalid_status", str(exc), status_code=422) from exc

        log_activity(
            self.db,
            user_id=user_id,
            action="task.move",
            entity_type="task",
            entity_id=task.id,
            details={"status": task.status},
            ip_address=ip_address,
        )
        self.db.commit()
        self.db.refresh(task)
        return task

    def get_kanban_board(self, case_id: uuid.UUID) -> KanbanBoardResponse:
        self.get_case(case_id)
        tasks = self.list_case_tasks(case_id)
        columns: dict[str, list[KanbanTaskCard]] = {column: [] for column in KANBAN_COLUMNS}

        for task in tasks:
            assignee_name = None
            if task.assignee_id:
                user = self.db.get(User, task.assignee_id)
                assignee_name = user.username if user else None
            columns[db_status_to_api(task.status)].append(
                KanbanTaskCard(
                    id=task.id,
                    title=task.title,
                    assignee=assignee_name,
                    due_date=task.due_date,
                    urgency=task.urgency,
                )
            )

        return KanbanBoardResponse(columns=columns)

    def _user_exists(self, user_id: uuid.UUID) -> bool:
        return self.db.get(User, user_id) is not None

    def _recent_activities(
        self,
        *,
        entity_type: str | None = None,
        entity_id: uuid.UUID | None = None,
        limit: int = 10,
    ) -> list[ActivityItem]:
        query = select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit)
        if entity_type:
            query = query.where(AuditLog.entity_type == entity_type)
        if entity_id:
            query = query.where(AuditLog.entity_id == entity_id)

        logs = self.db.scalars(query).all()
        activities: list[ActivityItem] = []
        for entry in logs:
            username = "system"
            if entry.user_id:
                user = self.db.get(User, entry.user_id)
                if user:
                    username = user.username
            activities.append(
                ActivityItem(
                    id=entry.id,
                    action=entry.action,
                    user=username,
                    timestamp=entry.timestamp,
                )
            )
        return activities
