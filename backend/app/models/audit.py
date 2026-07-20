from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from .base import Base

class AuditLog(Base):
    """
    Records actions taken by investigators for court-ready auditing.
    """
    __tablename__ = 'audit_logs'
    
    id = Column(Integer, primary_key=True, index=True)
    investigator_id = Column(Integer, ForeignKey('investigators.id'), nullable=True)
    action = Column(String, index=True) # e.g. "VIEW_ANALYTICS", "EXPORT_REPORT"
    resource_path = Column(String) # the API endpoint accessed
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    details = Column(Text, nullable=True) # Additional context or IP address
    
    investigator = relationship("Investigator")
