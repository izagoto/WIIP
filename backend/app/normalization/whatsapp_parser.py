import os
import sqlite3
import zipfile
import base64
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from Crypto.Cipher import AES
from app.models.people import Person, Alias
from app.models.communications import Chat, Message, Group, GroupMember
from app.models.case_management import Evidence

class WhatsAppParser:
    def __init__(self, db_session: Session, evidence_id: int):
        self.db = db_session
        self.evidence_id = evidence_id
        
        import typing
        
        evidence_record = self.db.query(Evidence).filter(Evidence.id == evidence_id).first()
        if not evidence_record:
            raise ValueError(f"Evidence ID {evidence_id} not found")
            
        self.evidence = evidence_record
        self.case_id = int(self.evidence.case_id) if self.evidence.case_id else 0  # type: ignore

    def _decrypt_sdp(self) -> str:
        if not self.evidence.is_encrypted:  # type: ignore
            # If not encrypted, assume the file path is a regular sqlite DB
            return str(self.evidence.file_path)  # type: ignore
            
        # Parse encryption key
        key = base64.b64decode(str(self.evidence.encryption_key))  # type: ignore
        
        # Temp paths
        sdp_path = str(self.evidence.file_path)  # type: ignore
        temp_dir = os.path.dirname(sdp_path)
        decrypted_db_path = os.path.join(temp_dir, f"temp_decrypted_{self.evidence.id}.db")  # type: ignore
        
        # Open ZIP
        with zipfile.ZipFile(sdp_path, 'r') as sdp_zip:
            # Read metadata to get nonce and tag
            with sdp_zip.open("metadata.json") as meta_f:
                import json
                metadata = json.load(meta_f)
                nonce = base64.b64decode(metadata["nonce"])
                tag = base64.b64decode(metadata["tag"])
            
            with sdp_zip.open("data.enc") as enc_f:
                ciphertext = enc_f.read()
                
        # Decrypt
        cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
        plaintext = cipher.decrypt_and_verify(ciphertext, tag)
        
        # Write to temp db
        with open(decrypted_db_path, "wb") as f_out:
            f_out.write(plaintext)
            
        return decrypted_db_path

    def _secure_wipe(self, file_path: str):
        """Securely deletes the temp decrypted DB to maintain evidence integrity."""
        if not os.path.exists(file_path):
            return
        file_size = os.path.getsize(file_path)
        with open(file_path, "wb") as f:
            chunk_size = 65536
            for _ in range(0, file_size, chunk_size):
                f.write(os.urandom(min(chunk_size, file_size - f.tell())))
        os.remove(file_path)

    def parse(self):
        """Main execution method to parse the whatsapp DB and normalize it."""
        db_path = self._decrypt_sdp()
        
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # 1. Extract JIDs (People/Groups)
            jid_map = self.extract_people(cursor)
            
            # 2. Extract Chats
            chat_map = self.extract_chats_and_groups(cursor, jid_map)
            
            # 3. Extract Messages
            self.extract_messages(cursor, chat_map, jid_map)
            
            self.db.commit()
            
        finally:
            # Always ensure the temp decrypted file is securely wiped
            if self.evidence.is_encrypted:  # type: ignore
                self._secure_wipe(db_path)

    def extract_people(self, cursor) -> Dict[int, Any]:
        """
        Parses the 'jid' table. WhatsApp stores contacts and group JIDs here.
        Returns a mapping of JID row_id to the created Person/Group object.
        """
        jid_map = {}
        try:
            cursor.execute("SELECT _id, raw_string FROM jid")
            jids = cursor.fetchall()
            
            for row in jids:
                row_id = row["_id"]
                raw_string = row["raw_string"]
                
                if not raw_string:
                    continue
                    
                # Identify if it's a group or a person
                if "@g.us" in raw_string:
                    # It's a group
                    group = Group(
                        case_id=self.case_id,
                        group_jid=raw_string,
                        name=raw_string # Can be updated later from group tables if needed
                    )
                    self.db.add(group)
                    self.db.flush()
                    jid_map[row_id] = {"type": "group", "obj": group}
                else:
                    # It's a person/contact
                    person = Person(
                        case_id=self.case_id,
                        phone_number=raw_string.replace("@s.whatsapp.net", "")
                    )
                    self.db.add(person)
                    self.db.flush()
                    jid_map[row_id] = {"type": "person", "obj": person}
                    
        except sqlite3.OperationalError as e:
            print(f"Warning: jid table might not exist or schema difference. {e}")
            
        return jid_map

    def extract_chats_and_groups(self, cursor, jid_map) -> Dict[int, Chat]:
        """
        Parses the 'chat' table to link JIDs to Chat entities.
        """
        chat_map = {}
        try:
            cursor.execute("SELECT _id, jid_row_id FROM chat")
            chats = cursor.fetchall()
            
            for row in chats:
                chat_id = row["_id"]
                jid_row_id = row["jid_row_id"]
                
                mapped_entity = jid_map.get(jid_row_id)
                if not mapped_entity:
                    continue
                    
                chat = Chat(
                    case_id=self.case_id,
                    chat_type="group" if mapped_entity["type"] == "group" else "direct",
                    related_group_id=mapped_entity["obj"].id if mapped_entity["type"] == "group" else None
                )
                self.db.add(chat)
                self.db.flush()
                
                chat_map[chat_id] = chat
                
        except sqlite3.OperationalError as e:
            print(f"Warning: chat table schema error. {e}")
            
        return chat_map

    def extract_messages(self, cursor, chat_map, jid_map):
        """
        Parses the 'message' table.
        Converts timestamps and inserts into Unified Model Message table.
        """
        try:
            # Query standard Android msgstore.db fields
            cursor.execute('''
                SELECT _id, chat_row_id, sender_jid_row_id, timestamp, text_data, from_me 
                FROM message
            ''')
            messages = cursor.fetchall()
            
            for row in messages:
                chat_row_id = row["chat_row_id"]
                sender_jid_row_id = row["sender_jid_row_id"]
                timestamp_ms = row["timestamp"]
                text_content = row["text_data"]
                from_me = row["from_me"]
                
                chat = chat_map.get(chat_row_id)
                if not chat:
                    continue
                
                # Convert milliseconds to datetime object
                if timestamp_ms:
                    dt = datetime.fromtimestamp(timestamp_ms / 1000.0, tz=timezone.utc)
                else:
                    dt = datetime.now(timezone.utc)
                    
                sender_id = None
                if not from_me and sender_jid_row_id:
                    sender_entity = jid_map.get(sender_jid_row_id)
                    if sender_entity and sender_entity["type"] == "person":
                        sender_id = sender_entity["obj"].id
                        
                message = Message(
                    chat_id=chat.id,
                    sender_id=sender_id,
                    text_content=text_content,
                    timestamp=dt,
                    evidence_id=self.evidence_id
                )
                self.db.add(message)
                
        except sqlite3.OperationalError as e:
            print(f"Warning: message table schema error. {e}")
