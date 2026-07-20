import os
import pandas as pd
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors

from app.engines.behavior import BehaviorEngine
from app.engines.graph import GraphEngine

REPORT_DIR = "/tmp/wiip_reports"
os.makedirs(REPORT_DIR, exist_ok=True)

class ReportGenerator:
    def __init__(self, db: Session, case_id: int):
        self.db = db
        self.case_id = case_id
        
    def generate_excel(self) -> str:
        """
        Exports all normalized messages to an Excel file.
        """
        engine = BehaviorEngine(self.db, self.case_id)
        df = engine.get_messages_dataframe()
        
        file_path = os.path.join(REPORT_DIR, f"case_{self.case_id}_messages.xlsx")
        
        if df.empty:
            # Create an empty excel with headers if no data
            df = pd.DataFrame(columns=["id", "sender_id", "timestamp", "text_content", "chat_type"])
            
        # Using openpyxl engine
        df.to_excel(file_path, index=False, engine='openpyxl')
        return file_path
        
    def generate_pdf(self) -> str:
        """
        Generates a summary PDF report containing analytics insights.
        """
        file_path = os.path.join(REPORT_DIR, f"case_{self.case_id}_analytics_report.pdf")
        
        c = canvas.Canvas(file_path, pagesize=A4)
        width, height = A4
        
        # Header
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, height - 50, f"WIIP Digital Forensics - Analytical Report")
        c.setFont("Helvetica", 12)
        c.drawString(50, height - 70, f"Case ID: {self.case_id}")
        c.drawString(50, height - 85, f"Date Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Behavior Bursts
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, height - 120, "1. Behavioral Anomalies (Activity Bursts)")
        
        b_engine = BehaviorEngine(self.db, self.case_id)
        bursts = b_engine.detect_activity_bursts()
        
        c.setFont("Helvetica", 10)
        y_pos = height - 140
        if not bursts:
            c.drawString(60, y_pos, "No significant message bursts detected.")
        else:
            for b in bursts[:5]: # Top 5
                c.drawString(60, y_pos, f"Date: {b['date']} | Count: {b['message_count']} (Threshold: {b['threshold']:.2f})")
                y_pos -= 15
                
        # Graph Centrality
        y_pos -= 20
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, y_pos, "2. Network Graph Centrality (Key Actors)")
        
        g_engine = GraphEngine(self.db, self.case_id)
        metrics = g_engine.get_centrality_metrics()
        
        y_pos -= 20
        c.setFont("Helvetica-Bold", 11)
        c.drawString(60, y_pos, "Top Degree Centrality (Most Connections):")
        c.setFont("Helvetica", 10)
        y_pos -= 15
        
        for p in metrics.get("top_degree", [])[:5]:
            c.drawString(70, y_pos, f"Node: {p['node']} - Score: {p['score']:.4f}")
            y_pos -= 15
            
        c.save()
        return file_path
