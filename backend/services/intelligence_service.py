import uuid
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.core.config import get_project_root
from backend.core.cache import get_dashboard_cache
from backend.core.exceptions import AppError
from backend.models.audit_log import AuditLog
from backend.models.case import Case
from backend.models.evidence import Evidence
from backend.models.intelligence import ApkAnalysis, Document, GraphEdge, GraphNode, NerEntity
from backend.models.whatsapp import WhatsAppData, WhatsAppImport
from backend.modules.d6_operations.audit import log_activity
from backend.modules.d8_intelligence.graph_analysis import serialize_graph
from backend.modules.d8_intelligence.ner import load_document_text, run_graph_analysis, run_ner_extraction
from backend.modules.d8_intelligence.apk_analyzer import analyze_apk_file
from backend.schemas.intelligence import (
    ApkAnalysisRequest,
    ApkAnalysisResponse,
    ApkCertificateResponse,
    ApkComponentsResponse,
    CorrelationResultItem,
    DashboardMetrics,
    GraphEdgeResponse,
    GraphNodeResponse,
    GraphRequest,
    GraphResponse,
    IntelligenceDashboardResponse,
    JobStatus,
    LatencyMetrics,
    NerRequest,
    NerEntityResponse,
    NerResponse,
    ThreatIndicatorResponse,
)
from ml.pipeline.inference import get_inference_pipeline


class IntelligenceService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.pipeline = get_inference_pipeline()

    def _resolve_path(self, url: str) -> Path:
        candidate = Path(url)
        if candidate.is_absolute() and candidate.exists():
            return candidate
        project_candidate = get_project_root() / url
        if project_candidate.exists():
            return project_candidate
        storage_candidate = Path(get_project_root() / "data" / "uploads" / url)
        if storage_candidate.exists():
            return storage_candidate
        raise AppError("file_not_found", f"File not found: {url}", status_code=422)

    def run_ner(
        self,
        payload: NerRequest,
        *,
        user_id: uuid.UUID,
        ip_address: str | None = None,
    ) -> NerResponse:
        if not self.db.get(Case, payload.case_id):
            raise AppError("invalid_case", "Case not found", status_code=422)

        file_path = self._resolve_path(payload.document_url)

        def handler(_: dict) -> dict:
            text = load_document_text(file_path, payload.document_type)
            return {"text": text, "entities": run_ner_extraction(text, list(payload.entity_types))}

        inference = self.pipeline.run(
            "ner",
            {
                "path": str(file_path),
                "document_type": payload.document_type,
                "entity_types": list(payload.entity_types),
            },
            handler,
        )
        text = inference.data["text"]
        entities = inference.data["entities"]

        document = Document(
            case_id=payload.case_id,
            file_name=file_path.name,
            file_type=payload.document_type,
            file_url=str(file_path),
            extracted_text=text,
        )
        self.db.add(document)
        self.db.flush()

        saved_entities: list[NerEntityResponse] = []
        for entity in entities:
            record = NerEntity(
                document_id=document.id,
                name=entity["name"],
                entity_type=entity["type"],
                confidence=Decimal(str(round(entity["confidence"], 2))),
                context=entity.get("context"),
            )
            self.db.add(record)
            saved_entities.append(
                NerEntityResponse(
                    name=entity["name"],
                    type=entity["type"],
                    confidence=entity["confidence"],
                    context=entity.get("context"),
                )
            )

        log_activity(
            self.db,
            user_id=user_id,
            action="intelligence.ner",
            entity_type="document",
            entity_id=document.id,
            details={"entity_count": len(saved_entities), "cache_hit": inference.cache_hit},
            ip_address=ip_address,
        )
        self.db.commit()

        return NerResponse(
            document_id=document.id,
            entities=saved_entities,
            processed_at=datetime.now(UTC),
        )

    def run_graph(
        self,
        payload: GraphRequest,
        *,
        user_id: uuid.UUID,
        ip_address: str | None = None,
    ) -> GraphResponse:
        def handler(_: dict) -> dict:
            result = run_graph_analysis(
                self.db,
                payload.source,
                payload.source_id,
                list(payload.entity_types),
            )
            return serialize_graph(result)

        inference = self.pipeline.run(
            "graph",
            {
                "source": payload.source,
                "source_id": str(payload.source_id),
                "entity_types": list(payload.entity_types),
            },
            handler,
            use_cache=False,
        )
        graph_data = inference.data
        graph_id = uuid.UUID(graph_data["graph_id"])

        for node in graph_data["nodes"]:
            self.db.add(
                GraphNode(
                    graph_id=graph_id,
                    node_id=node["id"],
                    label=node["label"],
                    node_type=node["type"],
                    properties=node.get("properties"),
                )
            )
        for edge in graph_data["edges"]:
            self.db.add(
                GraphEdge(
                    graph_id=graph_id,
                    source_node_id=edge["source"],
                    target_node_id=edge["target"],
                    weight=Decimal(str(round(edge["weight"], 2))),
                    relationship=edge["relationship"],
                )
            )

        log_activity(
            self.db,
            user_id=user_id,
            action="intelligence.graph",
            entity_type="graph",
            entity_id=graph_id,
            details={"node_count": len(graph_data["nodes"]), "edge_count": len(graph_data["edges"])},
            ip_address=ip_address,
        )
        self.db.commit()

        return GraphResponse(
            graph_id=graph_id,
            nodes=[GraphNodeResponse(**node) for node in graph_data["nodes"]],
            edges=[GraphEdgeResponse(**edge) for edge in graph_data["edges"]],
        )

    def run_apk_analysis(
        self,
        payload: ApkAnalysisRequest,
        *,
        user_id: uuid.UUID,
        ip_address: str | None = None,
    ) -> ApkAnalysisResponse:
        if not self.db.get(Case, payload.case_id):
            raise AppError("invalid_case", "Case not found", status_code=422)

        file_path = self._resolve_path(payload.apk_url)

        def handler(_: dict) -> dict:
            return analyze_apk_file(file_path)

        inference = self.pipeline.run(
            "apk",
            {"path": str(file_path), "filename": payload.apk_filename},
            handler,
        )
        analysis_data = inference.data

        document = Document(
            case_id=payload.case_id,
            file_name=payload.apk_filename,
            file_type="apk",
            file_url=str(file_path),
        )
        self.db.add(document)
        self.db.flush()

        record = ApkAnalysis(
            document_id=document.id,
            package_name=analysis_data.get("package_name"),
            version=analysis_data.get("version"),
            permissions=analysis_data.get("permissions"),
            components=analysis_data.get("components"),
            certificate=analysis_data.get("certificate"),
            threat_indicators=analysis_data.get("threat_indicators"),
        )
        self.db.add(record)
        self.db.flush()

        log_activity(
            self.db,
            user_id=user_id,
            action="intelligence.apk",
            entity_type="apk_analysis",
            entity_id=record.id,
            details={"package_name": record.package_name},
            ip_address=ip_address,
        )
        self.db.commit()
        self.db.refresh(record)

        certificate = None
        if analysis_data.get("certificate"):
            cert = analysis_data["certificate"]
            certificate = ApkCertificateResponse(
                issuer=str(cert.get("issuer", "unknown")),
                valid_from=datetime.fromisoformat(str(cert["valid_from"]).replace("Z", "+00:00")),
                valid_to=datetime.fromisoformat(str(cert["valid_to"]).replace("Z", "+00:00")),
            )

        return ApkAnalysisResponse(
            analysis_id=record.id,
            package_name=record.package_name,
            version=record.version,
            permissions=record.permissions or [],
            components=ApkComponentsResponse(**(record.components or {})),
            certificate=certificate,
            threat_indicators=[
                ThreatIndicatorResponse(**indicator)
                for indicator in (record.threat_indicators or [])
            ],
        )

    def get_dashboard(self, *, use_cache: bool = True) -> IntelligenceDashboardResponse:
        cache = get_dashboard_cache()
        cache_key = "intelligence_dashboard"
        if use_cache:
            cached = cache.get(cache_key)
            if cached is not None:
                return IntelligenceDashboardResponse(**{**cached, "cached": True})

        response = self._build_dashboard()
        cache.set(cache_key, response.model_dump(mode="json"), ttl_seconds=30)
        return response

    def _build_dashboard(self) -> IntelligenceDashboardResponse:
        total_documents = self.db.scalar(select(func.count()).select_from(Document)) or 0
        total_ner = self.db.scalar(select(func.count()).select_from(NerEntity)) or 0
        total_graphs = self.db.scalar(select(func.count(func.distinct(GraphNode.graph_id)))) or 0
        total_apk = self.db.scalar(select(func.count()).select_from(ApkAnalysis)) or 0
        total_cases = self.db.scalar(select(func.count()).select_from(Case)) or 0
        total_evidence = self.db.scalar(select(func.count()).select_from(Evidence)) or 0
        total_whatsapp = self.db.scalar(select(func.count()).select_from(WhatsAppData)) or 0
        cases_with_intelligence = (
            self.db.scalar(select(func.count(func.distinct(Document.case_id)))) or 0
        )

        queued = (
            self.db.scalar(
                select(func.count()).select_from(WhatsAppImport).where(WhatsAppImport.status == "queued")
            )
            or 0
        )
        running = (
            self.db.scalar(
                select(func.count()).select_from(WhatsAppImport).where(WhatsAppImport.status == "processing")
            )
            or 0
        )
        completed = (
            self.db.scalar(
                select(func.count()).select_from(WhatsAppImport).where(WhatsAppImport.status == "completed")
            )
            or 0
        )
        failed = (
            self.db.scalar(
                select(func.count()).select_from(WhatsAppImport).where(WhatsAppImport.status == "failed")
            )
            or 0
        )

        correlation_results: list[CorrelationResultItem] = []
        action_type_map = {
            "intelligence.ner": "ner",
            "intelligence.graph": "graph",
            "intelligence.apk": "apk",
            "case.intelligence.ner": "ner",
            "case.intelligence.graph": "graph",
        }
        for log in self.db.scalars(
            select(AuditLog)
            .where(AuditLog.action.in_(tuple(action_type_map.keys())))
            .order_by(AuditLog.timestamp.desc())
            .limit(10)
        ):
            result_type = action_type_map.get(log.action, "ner")
            entity_id = log.entity_id
            if entity_id is None:
                continue
            correlation_results.append(
                CorrelationResultItem(
                    id=entity_id,
                    type=result_type,  # type: ignore[arg-type]
                    status="completed",
                    created_at=log.timestamp,
                )
            )

        if not correlation_results:
            for document in self.db.scalars(
                select(Document).order_by(Document.created_at.desc()).limit(5)
            ):
                result_type = "apk" if document.file_type == "apk" else "ner"
                correlation_results.append(
                    CorrelationResultItem(
                        id=document.id,
                        type=result_type,
                        status="completed",
                        created_at=document.created_at,
                    )
                )

        pipeline = get_inference_pipeline()
        return IntelligenceDashboardResponse(
            metrics=DashboardMetrics(
                total_files_processed=total_documents,
                total_ner_extractions=total_ner,
                total_graph_analyses=total_graphs,
                total_apk_analyses=total_apk,
                total_cases=total_cases,
                total_evidence=total_evidence,
                total_whatsapp_conversations=total_whatsapp,
                cases_with_intelligence=cases_with_intelligence,
            ),
            job_status=JobStatus(
                queued=queued,
                running=running,
                completed=completed,
                failed=failed,
            ),
            correlation_results=correlation_results,
            latency=LatencyMetrics(
                average_ms=pipeline.stats.average_ms,
                p95_ms=pipeline.stats.p95_ms,
                p99_ms=pipeline.stats.p99_ms,
            ),
            generated_at=datetime.now(UTC),
            cached=False,
        )
