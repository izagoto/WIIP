from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from .base import Base

class Investigator(Base):
    __tablename__ = 'investigators'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    role = Column(String, default="investigator")
    
    cases = relationship("Case", back_populates="investigator")
    actions = relationship("ChainOfCustody", back_populates="investigator")

class Case(Base):
    __tablename__ = 'cases'
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(Text, nullable=True)
    status = Column(String, default="open") # open, closed, archived
    investigator_id = Column(Integer, ForeignKey('investigators.id'))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    investigator = relationship("Investigator", back_populates="cases")
    evidences = relationship("Evidence", back_populates="case")

class Evidence(Base):
    __tablename__ = 'evidences'
    
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey('cases.id'))
    source_type = Column(String) # e.g., whatsapp_db, media_file, contacts_db
    file_path = Column(String)
    file_size = Column(Integer, nullable=True) # in bytes
    file_hash = Column(String, index=True) # SHA256 hash for integrity
    md5_hash = Column(String, index=True, nullable=True) # MD5 hash
    file_metadata = Column(Text, nullable=True) # JSON string for extra metadata
    status = Column(String, default="pending") # pending, processing, processed, error
    is_encrypted = Column(Integer, default=0) # 0 for false, 1 for true
    encryption_key = Column(String, nullable=True) # Base64 encoded AES key
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    case = relationship("Case", back_populates="evidences")
    chain_of_custody = relationship("ChainOfCustody", back_populates="evidence")

class ChainOfCustody(Base):
    __tablename__ = 'chain_of_custody'
    
    id = Column(Integer, primary_key=True, index=True)
    evidence_id = Column(Integer, ForeignKey('evidences.id'))
    investigator_id = Column(Integer, ForeignKey('investigators.id'))
    action = Column(String) # e.g., imported, processed, viewed, exported
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    notes = Column(Text, nullable=True)
    
    evidence = relationship("Evidence", back_populates="chain_of_custody")
    investigator = relationship("Investigator", back_populates="actions")
