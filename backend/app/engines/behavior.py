import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Dict, Any, List
from app.models.communications import Message

class BehaviorEngine:
    def __init__(self, db: Session, case_id: int):
        self.db = db
        self.case_id = case_id
        
    def get_messages_dataframe(self) -> pd.DataFrame:
        """
        Extracts all messages for a specific case into a Pandas DataFrame for analysis.
        """
        # We use a raw SQL query with SQLAlchemy for fast bulk extraction into Pandas
        query = text("""
            SELECT m.id, m.sender_id, m.timestamp, m.text_content, c.chat_type
            FROM messages m
            JOIN chats c ON m.chat_id = c.id
            WHERE c.case_id = :case_id
        """)
        
        # Execute and load into DataFrame
        result = self.db.execute(query, {"case_id": self.case_id})
        df = pd.DataFrame(result.fetchall(), columns=["id", "sender_id", "timestamp", "text_content", "chat_type"])
        
        # Ensure timestamp is datetime
        if not df.empty:
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            
        return df
        
    def detect_activity_bursts(self) -> List[Dict[str, Any]]:
        """
        Detects sudden spikes in messaging activity by grouping by Date.
        """
        df = self.get_messages_dataframe()
        if df.empty:
            return []
            
        # Group by date
        df['date'] = df['timestamp'].dt.date  # type: ignore
        daily_counts = df.groupby('date').size().reset_index(name='message_count')
        
        # Calculate mean and std deviation to find bursts (anomalies)
        mean_count = daily_counts['message_count'].mean()
        std_count = daily_counts['message_count'].std()
        
        # Threshold for burst: more than 2 standard deviations above mean
        threshold = mean_count + (2 * std_count)
        
        bursts = daily_counts[daily_counts['message_count'] > threshold]
        
        results = []
        for _, row in bursts.iterrows():
            results.append({
                "date": str(row['date']),
                "message_count": int(row['message_count']),
                "threshold": threshold,
                "is_anomaly": True
            })
            
        return results
        
    def profile_active_hours(self, person_id: int) -> Dict[int, int]:
        """
        Profiles the active hours of a specific person (0-23 hours).
        Helps in identifying timezone or sleep patterns.
        """
        df = self.get_messages_dataframe()
        if df.empty:
            return {}
            
        # Filter for specific person
        person_df = df[df['sender_id'] == person_id].copy()
        if person_df.empty:
            return {}
            
        # Extract hour
        person_df.loc[:, 'hour'] = person_df['timestamp'].dt.hour  # type: ignore
        
        # Count by hour
        hourly_counts = person_df.groupby('hour').size().to_dict()
        
        # Ensure all 24 hours are represented
        return {hour: hourly_counts.get(hour, 0) for hour in range(24)}
