from ml.graph.visualization import graph_to_dict


def serialize_graph(result) -> dict:
    return graph_to_dict(result)
