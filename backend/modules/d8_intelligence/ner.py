from pathlib import Path

from ml.graph.analyzer import build_document_graph, build_whatsapp_graph
from ml.ner.model import extract_entities
from ml.utils.csv_processor import read_csv_text, read_text_file
from ml.utils.pdf_extractor import extract_pdf_text


def run_ner_extraction(text: str, entity_types: list[str]) -> list[dict]:
    entities = extract_entities(text, entity_types)
    return [
        {
            "name": entity.name,
            "type": entity.entity_type,
            "confidence": entity.confidence,
            "context": entity.context,
        }
        for entity in entities
    ]


def load_document_text(path: Path, document_type: str) -> str:
    if document_type == "csv":
        return read_csv_text(path)
    if document_type == "pdf":
        return extract_pdf_text(path)
    return read_text_file(path)


def run_graph_analysis(db, source: str, source_id, entity_types: list[str]):
    if source == "whatsapp":
        return build_whatsapp_graph(db, source_id, entity_types)
    return build_document_graph(db, source_id, entity_types)
