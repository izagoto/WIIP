from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Text
from sqlalchemy.orm import relationship
from .base import Base

class Location(Base):
    __tablename__ = 'locations'
    
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey('cases.id'))
    latitude = Column(Float)
    longitude = Column(Float)
    name = Column(String, nullable=True)
    address = Column(Text, nullable=True)
    timestamp = Column(DateTime, index=True)
    shared_in_message_id = Column(Integer, ForeignKey('messages.id'), nullable=True)
    evidence_id = Column(Integer, ForeignKey('evidences.id'))

class Media(Base):
    __tablename__ = 'media'
    
    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey('messages.id'), nullable=True)
    media_type = Column(String) # image, video, audio, document
    file_path = Column(String)
    file_hash = Column(String, index=True)
    file_size = Column(Integer)
    ocr_text = Column(Text, nullable=True)
    evidence_id = Column(Integer, ForeignKey('evidences.id'))
