from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from .base import Base

class Group(Base):
    __tablename__ = 'groups'
    
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey('cases.id'))
    group_jid = Column(String, index=True) # e.g. WhatsApp Group JID
    name = Column(String)
    creation_time = Column(DateTime, nullable=True)
    
    members = relationship("GroupMember", back_populates="group")
    chats = relationship("Chat", back_populates="group")

class GroupMember(Base):
    __tablename__ = 'group_members'
    
    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey('groups.id'))
    person_id = Column(Integer, ForeignKey('people.id'))
    role = Column(String, default="member") # admin, creator, member
    join_time = Column(DateTime, nullable=True)
    leave_time = Column(DateTime, nullable=True)
    
    group = relationship("Group", back_populates="members")

class Chat(Base):
    """
    A conversation thread. Can be direct (1-on-1) or group.
    """
    __tablename__ = 'chats'
    
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey('cases.id'))
    chat_type = Column(String) # direct, group
    related_group_id = Column(Integer, ForeignKey('groups.id'), nullable=True)
    
    group = relationship("Group", back_populates="chats")
    messages = relationship("Message", back_populates="chat")

class Message(Base):
    __tablename__ = 'messages'
    
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey('chats.id'))
    sender_id = Column(Integer, ForeignKey('people.id'))
    text_content = Column(Text, nullable=True)
    timestamp = Column(DateTime, index=True)
    is_deleted = Column(Boolean, default=False)
    is_forwarded = Column(Boolean, default=False)
    reply_to_message_id = Column(Integer, ForeignKey('messages.id'), nullable=True)
    evidence_id = Column(Integer, ForeignKey('evidences.id'))
    
    chat = relationship("Chat", back_populates="messages")
    replies = relationship("Message", backref="parent_message", remote_side=[id])

class Call(Base):
    __tablename__ = 'calls'
    
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey('cases.id'))
    caller_id = Column(Integer, ForeignKey('people.id'))
    receiver_id = Column(Integer, ForeignKey('people.id'))
    call_type = Column(String) # audio, video
    start_time = Column(DateTime, index=True)
    duration = Column(Integer) # in seconds
    evidence_id = Column(Integer, ForeignKey('evidences.id'))
