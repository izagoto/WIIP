from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from .base import Base

class Person(Base):
    """
    Represents a normalized individual across different chats/evidences.
    """
    __tablename__ = 'people'
    
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey('cases.id'))
    phone_number = Column(String, index=True)
    first_seen = Column(DateTime, nullable=True)
    last_seen = Column(DateTime, nullable=True)
    activity_score = Column(Float, default=0.0)
    
    aliases = relationship("Alias", back_populates="person")
    devices = relationship("Device", back_populates="person")

class Alias(Base):
    """
    Because one person can be saved with different names in different contact lists.
    """
    __tablename__ = 'aliases'
    
    id = Column(Integer, primary_key=True, index=True)
    person_id = Column(Integer, ForeignKey('people.id'))
    name = Column(String, index=True)
    evidence_id = Column(Integer, ForeignKey('evidences.id'))
    
    person = relationship("Person", back_populates="aliases")

class Device(Base):
    """
    Device information associated with a person.
    """
    __tablename__ = 'devices'
    
    id = Column(Integer, primary_key=True, index=True)
    person_id = Column(Integer, ForeignKey('people.id'))
    device_type = Column(String) # iOS, Android, Web
    os_info = Column(String, nullable=True)
    evidence_id = Column(Integer, ForeignKey('evidences.id'))
    
    person = relationship("Person", back_populates="devices")
