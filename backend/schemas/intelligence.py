import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

EntityType = Literal["person", "location", "organization", "date"]
GraphEntityType = Literal["person", "contact", "location", "organization"]
GraphSource = Literal["whatsapp", "document"]
DocumentType = Literal["csv", "pdf"]
ThreatSeverity = Literal["low", "medium", "high", "critical"]


class NerRequest(BaseModel):
    case_id: uuid.UUID
    document_url: str = Field(min_length=1, max_length=500)
    document_type: DocumentType
    entity_types: list[EntityType] = Field(default_factory=lambda: ["person", "location", "organization", "date"])


class NerEntityResponse(BaseModel):
    name: str
    type: str
    confidence: float
    context: str | None


class NerResponse(BaseModel):
    document_id: uuid.UUID
    entities: list[NerEntityResponse]
    processed_at: datetime


class GraphRequest(BaseModel):
    source: GraphSource
    source_id: uuid.UUID
    entity_types: list[GraphEntityType] = Field(
        default_factory=lambda: ["person", "contact", "location"]
    )


class GraphNodeResponse(BaseModel):
    id: str
    label: str
    type: str
    properties: dict = Field(default_factory=dict)


class GraphEdgeResponse(BaseModel):
    source: str
    target: str
    weight: float
    relationship: str


class GraphResponse(BaseModel):
    graph_id: uuid.UUID
    nodes: list[GraphNodeResponse]
    edges: list[GraphEdgeResponse]


class ApkAnalysisRequest(BaseModel):
    case_id: uuid.UUID
    apk_url: str = Field(min_length=1, max_length=500)
    apk_filename: str = Field(min_length=1, max_length=255)


class ApkComponentsResponse(BaseModel):
    activities: list[str] = Field(default_factory=list)
    services: list[str] = Field(default_factory=list)
    receivers: list[str] = Field(default_factory=list)
    providers: list[str] = Field(default_factory=list)


class ApkCertificateResponse(BaseModel):
    issuer: str
    valid_from: datetime
    valid_to: datetime


class ThreatIndicatorResponse(BaseModel):
    type: str
    description: str
    severity: ThreatSeverity


class ApkAnalysisResponse(BaseModel):
    analysis_id: uuid.UUID
    package_name: str | None
    version: str | None
    permissions: list[str]
    components: ApkComponentsResponse
    certificate: ApkCertificateResponse | None
    threat_indicators: list[ThreatIndicatorResponse]


class DashboardMetrics(BaseModel):
    total_files_processed: int
    total_ner_extractions: int
    total_graph_analyses: int
    total_apk_analyses: int
    total_cases: int
    total_evidence: int
    total_whatsapp_conversations: int
    cases_with_intelligence: int


class JobStatus(BaseModel):
    queued: int
    running: int
    completed: int
    failed: int


class CorrelationResultItem(BaseModel):
    id: uuid.UUID
    type: Literal["ner", "graph", "apk"]
    status: Literal["completed", "failed"]
    created_at: datetime


class LatencyMetrics(BaseModel):
    average_ms: int
    p95_ms: int
    p99_ms: int


class IntelligenceDashboardResponse(BaseModel):
    metrics: DashboardMetrics
    job_status: JobStatus
    correlation_results: list[CorrelationResultItem]
    latency: LatencyMetrics
    generated_at: datetime
    cached: bool = False


class CaseModuleCounts(BaseModel):
    whatsapp_conversations: int
    whatsapp_messages: int
    evidence_items: int
    documents_analyzed: int
    ner_entities: int
    graph_analyses: int
    apk_analyses: int
    custody_entries: int


class CaseIntegrationResponse(BaseModel):
    case_id: uuid.UUID
    title: str
    status: str
    priority: str
    modules: CaseModuleCounts
    intelligence_ready: bool
    reports_available: list[str]
    latest_correlations: list[CorrelationResultItem]


class CaseAnalyzeRequest(BaseModel):
    run_graph: bool = True
    document_url: str | None = Field(default=None, max_length=500)
    document_type: DocumentType | None = None
    entity_types: list[EntityType] = Field(
        default_factory=lambda: ["person", "location", "organization", "date"]
    )


class CaseAnalyzeResponse(BaseModel):
    case_id: uuid.UUID
    graph: GraphResponse | None = None
    ner: NerResponse | None = None
    analyzed_at: datetime
