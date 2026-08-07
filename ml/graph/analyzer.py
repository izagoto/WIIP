from __future__ import annotations

import uuid
from collections import defaultdict
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models.intelligence import NerEntity
from backend.models.whatsapp import WhatsAppData, WhatsAppMessage


@dataclass
class GraphNodeData:
    id: str
    label: str
    node_type: str
    properties: dict | None = None


@dataclass
class GraphEdgeData:
    source: str
    target: str
    weight: float
    relationship: str


@dataclass
class GraphResult:
    graph_id: uuid.UUID
    nodes: list[GraphNodeData]
    edges: list[GraphEdgeData]


def build_whatsapp_graph(
    db: Session,
    source_id: uuid.UUID,
    entity_types: list[str] | None = None,
) -> GraphResult:
    allowed = set(entity_types or ["person", "contact", "location"])
    graph_id = uuid.uuid4()

    conversations = list(
        db.scalars(select(WhatsAppData).where(WhatsAppData.case_id == source_id))
    )
    if not conversations:
        conversation = db.get(WhatsAppData, source_id)
        if conversation:
            conversations = [conversation]

    nodes: dict[str, GraphNodeData] = {}
    edge_weights: dict[tuple[str, str], int] = defaultdict(int)

    for conversation in conversations:
        contact_id = f"contact:{conversation.wa_chat_jid}"
        contact_label = conversation.contact or conversation.group_name or conversation.wa_chat_jid
        if "contact" in allowed:
            nodes[contact_id] = GraphNodeData(
                id=contact_id,
                label=contact_label,
                node_type="contact",
                properties={"wa_chat_jid": conversation.wa_chat_jid},
            )

        messages = list(
            db.scalars(
                select(WhatsAppMessage).where(
                    WhatsAppMessage.conversation_record_id == conversation.id
                )
            )
        )
        for message in messages:
            sender_id = f"person:{message.sender}"
            receiver_id = f"person:{message.receiver}"
            if "person" in allowed:
                nodes.setdefault(
                    sender_id,
                    GraphNodeData(id=sender_id, label=message.sender, node_type="person"),
                )
                nodes.setdefault(
                    receiver_id,
                    GraphNodeData(id=receiver_id, label=message.receiver, node_type="person"),
                )
            edge_weights[(sender_id, receiver_id)] += 1
            if contact_id in nodes:
                edge_weights[(sender_id, contact_id)] += 1

    edges = [
        GraphEdgeData(
            source=source,
            target=target,
            weight=float(weight),
            relationship="communicated_with",
        )
        for (source, target), weight in edge_weights.items()
        if source in nodes and target in nodes
    ]

    return GraphResult(graph_id=graph_id, nodes=list(nodes.values()), edges=edges)


def build_document_graph(
    db: Session,
    source_id: uuid.UUID,
    entity_types: list[str] | None = None,
) -> GraphResult:
    allowed = set(entity_types or ["person", "contact", "location", "organization"])
    graph_id = uuid.uuid4()

    entities = list(
        db.scalars(select(NerEntity).where(NerEntity.document_id == source_id))
    )
    nodes: dict[str, GraphNodeData] = {}
    edge_weights: dict[tuple[str, str], int] = defaultdict(int)

    for entity in entities:
        if entity.entity_type not in allowed:
            continue
        node_id = f"{entity.entity_type}:{entity.name.lower()}"
        nodes[node_id] = GraphNodeData(
            id=node_id,
            label=entity.name,
            node_type=entity.entity_type,
            properties={"confidence": float(entity.confidence or 0)},
        )

    grouped: dict[str, list[NerEntity]] = defaultdict(list)
    for entity in entities:
        if entity.entity_type in allowed:
            grouped[entity.entity_type].append(entity)

    for entity_list in grouped.values():
        for left in entity_list:
            for right in entity_list:
                if left.id == right.id:
                    continue
                left_id = f"{left.entity_type}:{left.name.lower()}"
                right_id = f"{right.entity_type}:{right.name.lower()}"
                edge_weights[(left_id, right_id)] += 1

    edges = [
        GraphEdgeData(
            source=source,
            target=target,
            weight=float(weight),
            relationship="co_occurs",
        )
        for (source, target), weight in edge_weights.items()
        if source in nodes and target in nodes
    ]

    return GraphResult(graph_id=graph_id, nodes=list(nodes.values()), edges=edges)
