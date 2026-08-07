import re

from dataclasses import dataclass

from ml.ner.preprocessing import normalize_text


@dataclass
class ExtractedEntity:
    name: str
    entity_type: str
    confidence: float
    context: str


ENTITY_PATTERNS: dict[str, list[str]] = {
    "date": [
        r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
        r"\b\d{4}-\d{2}-\d{2}\b",
        r"\b(?:Januari|Februari|Maret|April|Mei|Juni|Juli|Agustus|September|Oktober|November|Desember)\s+\d{4}\b",
    ],
    "person": [
        r"\b(?:Bapak|Ibu|Pak|Bu|Mr|Mrs|Dr)\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b",
        r"\b[A-Z][a-z]+\s+[A-Z][a-z]+\b",
    ],
    "location": [
        r"\b(?:Jakarta|Surabaya|Bandung|Medan|Semarang|Makassar|Bali|Indonesia|Yogyakarta)\b",
    ],
    "organization": [
        r"\b(?:PT|CV|UD)\s+[A-Za-z0-9][A-Za-z0-9\s&\.]{2,}\b",
    ],
}


def _extract_with_regex(text: str, entity_types: list[str]) -> list[ExtractedEntity]:
    entities: list[ExtractedEntity] = []
    seen: set[tuple[str, str]] = set()

    for entity_type in entity_types:
        patterns = ENTITY_PATTERNS.get(entity_type, [])
        for pattern in patterns:
            for match in re.finditer(pattern, text):
                name = match.group(0).strip()
                key = (name.lower(), entity_type)
                if key in seen:
                    continue
                seen.add(key)
                start = max(0, match.start() - 30)
                end = min(len(text), match.end() + 30)
                entities.append(
                    ExtractedEntity(
                        name=name,
                        entity_type=entity_type,
                        confidence=0.75,
                        context=text[start:end].strip(),
                    )
                )
    return entities


def _extract_with_spacy(text: str, entity_types: list[str]) -> list[ExtractedEntity]:
    try:
        import spacy
    except ImportError:
        return []

    try:
        nlp = spacy.load("id_core_news_sm")
    except OSError:
        return []

    label_map = {
        "PERSON": "person",
        "ORG": "organization",
        "GPE": "location",
        "LOC": "location",
        "DATE": "date",
    }
    allowed = set(entity_types)
    entities: list[ExtractedEntity] = []
    seen: set[tuple[str, str]] = set()

    for ent in nlp(text).ents:
        mapped = label_map.get(ent.label_)
        if not mapped or mapped not in allowed:
            continue
        key = (ent.text.lower(), mapped)
        if key in seen:
            continue
        seen.add(key)
        start = max(0, ent.start_char - 30)
        end = min(len(text), ent.end_char + 30)
        entities.append(
            ExtractedEntity(
                name=ent.text.strip(),
                entity_type=mapped,
                confidence=0.9,
                context=text[start:end].strip(),
            )
        )
    return entities


def extract_entities(text: str, entity_types: list[str] | None = None) -> list[ExtractedEntity]:
    normalized = normalize_text(text)
    if not normalized:
        return []

    selected_types = entity_types or list(ENTITY_PATTERNS.keys())
    spacy_entities = _extract_with_spacy(normalized, selected_types)
    if spacy_entities:
        return spacy_entities
    return _extract_with_regex(normalized, selected_types)
