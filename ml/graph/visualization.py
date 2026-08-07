from ml.graph.analyzer import GraphResult


def graph_to_dict(result: GraphResult) -> dict:
    return {
        "graph_id": str(result.graph_id),
        "nodes": [
            {
                "id": node.id,
                "label": node.label,
                "type": node.node_type,
                "properties": node.properties or {},
            }
            for node in result.nodes
        ],
        "edges": [
            {
                "source": edge.source,
                "target": edge.target,
                "weight": edge.weight,
                "relationship": edge.relationship,
            }
            for edge in result.edges
        ],
    }
