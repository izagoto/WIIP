from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Any
from app.models.communications import Group, Chat, Message
from app.models.people import Person, Alias

class CorrelationEngine:
    def __init__(self, db: Session, case_id: int):
        self.db = db
        self.case_id = case_id
        
    def find_common_groups(self, person_id_1: int, person_id_2: int) -> List[Dict[str, Any]]:
        """
        Since we haven't fully parsed group members yet (only JIDs), we can correlate
        based on participants in a group chat, but for now we look at the Group/Chat models.
        (A complete group member parser is needed for this to be 100% accurate, but here is the logic).
        """
        # Placeholder logic: Find groups where both persons have sent messages.
        # This is a strong indicator they are in the same group.
        
        # Subquery: Groups where person 1 sent a message
        p1_groups = self.db.query(Chat.related_group_id).join(Message, Message.chat_id == Chat.id)\
            .filter(Chat.case_id == self.case_id)\
            .filter(Message.sender_id == person_id_1)\
            .filter(Chat.chat_type == "group").distinct()
            
        # Subquery: Groups where person 2 sent a message
        p2_groups = self.db.query(Chat.related_group_id).join(Message, Message.chat_id == Chat.id)\
            .filter(Chat.case_id == self.case_id)\
            .filter(Message.sender_id == person_id_2)\
            .filter(Chat.chat_type == "group").distinct()
            
        # Intersection
        common_group_ids = set(p1.related_group_id for p1 in p1_groups).intersection(
            set(p2.related_group_id for p2 in p2_groups)
        )
        
        results = []
        for gid in common_group_ids:
            group = self.db.query(Group).filter(Group.id == gid).first()
            if group:
                results.append({
                    "group_id": group.id,
                    "group_name": group.name,
                    "group_jid": group.group_jid
                })
                
        return results

    def trace_forwarded_messages(self, text_snippet: str) -> List[Dict[str, Any]]:
        """
        Finds messages matching a specific text (e.g. viral hoax or chain command)
        to see who forwarded it to whom.
        """
        messages = self.db.query(Message, Person, Chat)\
            .join(Person, Message.sender_id == Person.id)\
            .join(Chat, Message.chat_id == Chat.id)\
            .filter(Chat.case_id == self.case_id)\
            .filter(Message.text_content.ilike(f"%{text_snippet}%"))\
            .order_by(Message.timestamp.asc())\
            .all()
            
        trace = []
        for msg, person, chat in messages:
            trace.append({
                "message_id": msg.id,
                "timestamp": msg.timestamp,
                "sender_phone": person.phone_number,
                "chat_id": chat.id,
                "chat_type": chat.chat_type,
                "text": msg.text_content
            })
            
        return trace
