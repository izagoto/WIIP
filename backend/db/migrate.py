import logging
from datetime import UTC, datetime
from collections import defaultdict

from sqlalchemy import inspect, select, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from backend.models.case import Case
from backend.models.evidence import Evidence
from backend.modules.d6_operations.reference_number import format_reference_number, wib_day_bounds_utc
from backend.modules.d7_evidence.categories import derive_category
from backend.modules.d7_evidence.registration_number import format_registration_number

logger = logging.getLogger(__name__)

_LEGACY_CATEGORY_TYPES = {"mobile", "device", "document", "media"}


def run_migrations(engine: Engine) -> None:
    _migrate_cases_table(engine)
    _migrate_evidence_table(engine)


def _migrate_cases_table(engine: Engine) -> None:
    inspector = inspect(engine)
    if "cases" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("cases")}
    statements: list[str] = []

    if "reference_number" not in columns:
        statements.append("ALTER TABLE cases ADD COLUMN reference_number VARCHAR(50)")
    if "registered_at" not in columns:
        statements.append("ALTER TABLE cases ADD COLUMN registered_at DATETIME")

    if statements:
        with engine.begin() as connection:
            for statement in statements:
                connection.execute(text(statement))

    with Session(engine) as session:
        cases = list(session.scalars(select(Case).order_by(Case.created_at.asc())))
        daily_counters: dict[str, int] = defaultdict(int)
        changed = False

        for case in cases:
            if not case.reference_number:
                created_at = case.created_at or datetime.now(UTC)
                start_utc, end_utc = wib_day_bounds_utc(created_at)
                day_key = start_utc.isoformat()
                daily_counters[day_key] += 1
                case.reference_number = format_reference_number(
                    case.title,
                    created_at,
                    daily_counters[day_key],
                )
                changed = True
            if case.registered_at is None:
                case.registered_at = case.created_at or datetime.now(UTC)
                changed = True

        if changed:
            session.commit()
            logger.info("Backfilled case reference_number and registered_at columns")


def _migrate_evidence_table(engine: Engine) -> None:
    inspector = inspect(engine)
    if "evidence" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("evidence")}
    statements: list[str] = []

    if "registration_number" not in columns:
        statements.append("ALTER TABLE evidence ADD COLUMN registration_number VARCHAR(50)")
    if "received_at" not in columns:
        statements.append("ALTER TABLE evidence ADD COLUMN received_at DATETIME")
    if "imei_slot1" not in columns:
        statements.append("ALTER TABLE evidence ADD COLUMN imei_slot1 VARCHAR(25)")
    if "imei_slot2" not in columns:
        statements.append("ALTER TABLE evidence ADD COLUMN imei_slot2 VARCHAR(25)")
    if "category" not in columns:
        statements.append("ALTER TABLE evidence ADD COLUMN category VARCHAR(20)")

    if statements:
        with engine.begin() as connection:
            for statement in statements:
                connection.execute(text(statement))

    with engine.begin() as connection:
        refreshed_columns = {column["name"] for column in inspect(connection).get_columns("evidence")}
        if "imei" in refreshed_columns and "imei_slot1" in refreshed_columns:
            connection.execute(
                text(
                    "UPDATE evidence SET imei_slot1 = imei "
                    "WHERE (imei_slot1 IS NULL OR imei_slot1 = '') AND imei IS NOT NULL AND imei != ''"
                )
            )
        if "item_type" in refreshed_columns:
            connection.execute(
                text(
                    "UPDATE evidence SET type = item_type "
                    "WHERE item_type IS NOT NULL AND item_type != '' "
                    "AND type IN ('mobile', 'device', 'document', 'media')"
                )
            )
            connection.execute(
                text(
                    "UPDATE evidence SET type = 'Smartphone' "
                    "WHERE type = 'mobile' AND (item_type IS NULL OR item_type = '')"
                )
            )
            connection.execute(text("UPDATE evidence SET type = 'Dokumen' WHERE type = 'document'"))
            connection.execute(text("UPDATE evidence SET type = 'Media Digital' WHERE type = 'media'"))
            connection.execute(text("UPDATE evidence SET type = 'Perangkat Elektronik' WHERE type = 'device'"))
        if "category" in refreshed_columns:
            connection.execute(
                text(
                    "UPDATE evidence SET category = type "
                    "WHERE (category IS NULL OR category = '') "
                    "AND type IN ('mobile', 'device', 'document', 'media')"
                )
            )
            connection.execute(
                text("UPDATE evidence SET category = 'mobile' WHERE category IS NULL OR category = ''")
            )

    with Session(engine) as session:
        evidence_items = list(session.scalars(select(Evidence).order_by(Evidence.created_at.asc())))
        daily_counters: dict[str, int] = defaultdict(int)
        changed = False

        for evidence in evidence_items:
            received_at = evidence.received_at or evidence.created_at or datetime.now(UTC)
            if evidence.received_at is None:
                evidence.received_at = received_at
                changed = True

            legacy_imei = getattr(evidence, "imei", None)
            if not evidence.imei_slot1 and legacy_imei:
                evidence.imei_slot1 = legacy_imei
                changed = True

            legacy_item_type = getattr(evidence, "item_type", None)
            if legacy_item_type and evidence.type in _LEGACY_CATEGORY_TYPES:
                evidence.type = legacy_item_type
                changed = True
            elif evidence.type in _LEGACY_CATEGORY_TYPES:
                evidence.type = {
                    "mobile": "Smartphone",
                    "device": "Perangkat Elektronik",
                    "document": "Dokumen",
                    "media": "Media Digital",
                }.get(evidence.type, evidence.type)
                changed = True

            if not evidence.category or evidence.category in _LEGACY_CATEGORY_TYPES:
                evidence.category = derive_category(evidence.type)
                changed = True

            if not evidence.registration_number:
                start_utc, end_utc = wib_day_bounds_utc(received_at)
                day_key = start_utc.isoformat()
                daily_counters[day_key] += 1
                evidence.registration_number = format_registration_number(
                    received_at,
                    daily_counters[day_key],
                )
                changed = True

        if changed:
            session.commit()
            logger.info("Backfilled evidence registration and smartphone fields")
