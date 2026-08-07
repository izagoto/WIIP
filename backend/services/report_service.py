import uuid
from datetime import UTC, datetime
from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.core.exceptions import NotFoundError
from backend.models.audit_log import AuditLog
from backend.models.case import Case
from backend.models.custody import CustodyLog
from backend.models.evidence import Evidence
from backend.models.task import Task
from backend.models.user import User


class ReportService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def generate_case_report_pdf(self, case_id: uuid.UUID) -> bytes:
        case = self.db.get(Case, case_id)
        if not case:
            raise NotFoundError("Case not found")

        task_count = self.db.scalar(select(func.count()).select_from(Task).where(Task.case_id == case_id)) or 0
        done_count = (
            self.db.scalar(
                select(func.count())
                .select_from(Task)
                .where(Task.case_id == case_id, Task.status == "done")
            )
            or 0
        )
        evidence_count = (
            self.db.scalar(select(func.count()).select_from(Evidence).where(Evidence.case_id == case_id)) or 0
        )

        assignee_name = "—"
        if case.assigned_to:
            user = self.db.get(User, case.assigned_to)
            if user:
                assignee_name = user.username

        creator_name = "—"
        if case.created_by:
            user = self.db.get(User, case.created_by)
            if user:
                creator_name = user.username

        recent_activity = list(
            self.db.scalars(
                select(AuditLog)
                .where(AuditLog.entity_type == "case", AuditLog.entity_id == case_id)
                .order_by(AuditLog.timestamp.desc())
                .limit(10)
            )
        )

        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        y = height - 50

        def writeln(text: str, *, indent: int = 50, size: int = 11, gap: int = 16) -> None:
            nonlocal y
            if y < 80:
                pdf.showPage()
                y = height - 50
            pdf.setFont("Helvetica", size)
            pdf.drawString(indent, y, text[:110])
            y -= gap

        pdf.setFont("Helvetica-Bold", 16)
        pdf.drawString(50, y, "Evidentra — Case Investigation Report")
        y -= 28

        writeln(f"Generated: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}", size=9, gap=22)
        writeln(f"Case ID: {case.id}")
        writeln(f"Title: {case.title}")
        writeln(f"Status: {case.status}")
        writeln(f"Priority: {case.priority}")
        writeln(f"Assigned unit: {case.assigned_unit or '—'}")
        writeln(f"Assigned investigator: {assignee_name}")
        writeln(f"Created by: {creator_name}")
        writeln(f"Created at: {case.created_at}")
        writeln(f"Updated at: {case.updated_at}")
        y -= 8
        writeln("Description:", size=12, gap=14)
        description = case.description or "—"
        for line in _wrap_text(description, 90):
            writeln(line, indent=60, size=10, gap=14)

        y -= 8
        writeln("Summary", size=13, gap=18)
        writeln(f"Tasks: {done_count}/{task_count} completed")
        writeln(f"Evidence items: {evidence_count}")

        y -= 8
        writeln("Recent case activity", size=13, gap=18)
        if not recent_activity:
            writeln("No audit entries recorded for this case.", indent=60, size=10)
        else:
            for entry in recent_activity:
                ts = entry.timestamp.strftime("%Y-%m-%d %H:%M")
                writeln(f"{ts} — {entry.action}", indent=60, size=10, gap=14)

        pdf.save()
        buffer.seek(0)
        return buffer.getvalue()

    def generate_custody_report_pdf(self, evidence_ids: list[uuid.UUID]) -> bytes:
        if not evidence_ids:
            raise NotFoundError("No evidence specified for custody report")

        evidence_items: list[Evidence] = []
        for evidence_id in evidence_ids:
            evidence = self.db.get(Evidence, evidence_id)
            if not evidence:
                raise NotFoundError(f"Evidence not found: {evidence_id}")
            evidence_items.append(evidence)

        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        y = height - 50

        def writeln(text: str, *, indent: int = 50, size: int = 11, gap: int = 16) -> None:
            nonlocal y
            if y < 80:
                pdf.showPage()
                y = height - 50
            pdf.setFont("Helvetica", size)
            pdf.drawString(indent, y, text[:110])
            y -= gap

        pdf.setFont("Helvetica-Bold", 16)
        pdf.drawString(50, y, "Evidentra — Berita Acara Serah Terima (BAST)")
        y -= 28
        writeln(f"Generated: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}", size=9, gap=22)
        writeln(f"Evidence items: {len(evidence_items)}", gap=20)

        for evidence in evidence_items:
            case = self.db.get(Case, evidence.case_id)
            case_title = case.title if case else "—"
            y -= 8
            writeln(f"Evidence ID: {evidence.id}", size=12, gap=18)
            writeln(f"Case: {case_title}", indent=60, size=10)
            writeln(f"Type: {evidence.type} | Brand: {evidence.brand or '—'}", indent=60, size=10)
            writeln(f"Serial: {evidence.serial_number or '—'} | IMEI: {evidence.imei or '—'}", indent=60, size=10)
            writeln(f"Storage: {evidence.storage_location or '—'}", indent=60, size=10)
            writeln(f"SHA-256: {evidence.sha256_hash or 'not verified'}", indent=60, size=10, gap=14)

            logs = list(
                self.db.scalars(
                    select(CustodyLog)
                    .where(CustodyLog.evidence_id == evidence.id)
                    .order_by(CustodyLog.timestamp.asc(), CustodyLog.created_at.asc())
                )
            )
            writeln("Custody history:", indent=60, size=10, gap=14)
            if not logs:
                writeln("No custody entries recorded.", indent=70, size=9, gap=12)
            else:
                for log in logs:
                    holder = self._username(log.holder_id)
                    from_user = self._username(log.from_user_id)
                    to_user = self._username(log.to_user_id)
                    ts = log.timestamp.strftime("%Y-%m-%d %H:%M")
                    detail = f"{ts} — {log.action}"
                    if from_user and to_user:
                        detail += f" ({from_user} -> {to_user})"
                    elif holder:
                        detail += f" (holder: {holder})"
                    writeln(detail, indent=70, size=9, gap=12)

        pdf.save()
        buffer.seek(0)
        return buffer.getvalue()

    def _username(self, user_id: uuid.UUID | None) -> str | None:
        if not user_id:
            return None
        user = self.db.get(User, user_id)
        return user.username if user else None


def _wrap_text(text: str, width: int) -> list[str]:
    words = text.split()
    if not words:
        return ["—"]
    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        if len(candidate) <= width:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines
