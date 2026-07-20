import networkx as nx
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Dict, Any

class GraphEngine:
    def __init__(self, db: Session, case_id: int):
        self.db = db
        self.case_id = case_id
        
    def build_interaction_graph(self) -> nx.Graph:
        """
        Builds a NetworkX graph based on direct chats or group interactions.
        For MVP, we'll connect a sender to a chat ID, but ideally it should be
        Person to Person via 1-on-1 chats.
        """
        # We find direct 1-on-1 chats to draw edges between two people
        # However, WhatsApp DB structure stores it as Sender -> Chat. 
        # For a true graph, we link everyone who participated in a group, or 
        # link sender to receiver in direct chats.
        
        # Simplified query: Edge between sender and the "Chat Entity" 
        # (This creates a bipartite graph, which we can project)
        query = text("""
            SELECT m.sender_id, c.id as chat_id, c.chat_type
            FROM messages m
            JOIN chats c ON m.chat_id = c.id
            WHERE c.case_id = :case_id AND m.sender_id IS NOT NULL
        """)
        
        result = self.db.execute(query, {"case_id": self.case_id}).fetchall()
        
        # Bipartite Graph: Person Nodes and Chat Nodes
        B = nx.Graph()
        
        for row in result:
            person_node = f"P_{row.sender_id}"
            chat_node = f"C_{row.chat_id}"
            
            B.add_node(person_node, bipartite=0, type="person", id=row.sender_id)
            B.add_node(chat_node, bipartite=1, type=row.chat_type, id=row.chat_id)
            
            if B.has_edge(person_node, chat_node):
                B[person_node][chat_node]['weight'] += 1
            else:
                B.add_edge(person_node, chat_node, weight=1)
                
        # Project bipartite graph to just Person-to-Person relationships
        person_nodes = [n for n, d in B.nodes(data=True) if d.get('bipartite') == 0]
        
        # Two people are connected if they share a chat
        # For large data, bipartite projection is heavy, but works for MVP.
        G = nx.bipartite.projected_graph(B, person_nodes)
        return G

    def get_centrality_metrics(self) -> Dict[str, Any]:
        """
        Calculates Degree Centrality (who has the most connections) 
        and Betweenness Centrality (who acts as a bridge).
        """
        G = self.build_interaction_graph()
        
        if len(G.nodes) == 0:
            return {"degree_centrality": {}, "betweenness_centrality": {}}
            
        degree_cent = nx.degree_centrality(G)
        betweenness_cent = nx.betweenness_centrality(G)
        
        # Sort and return top 10
        sorted_degree = sorted(degree_cent.items(), key=lambda item: item[1], reverse=True)[:10]
        sorted_betweenness = sorted(betweenness_cent.items(), key=lambda item: item[1], reverse=True)[:10]
        
        return {
            "top_degree": [{"node": k, "score": v} for k, v in sorted_degree],
            "top_betweenness": [{"node": k, "score": v} for k, v in sorted_betweenness]
        }
