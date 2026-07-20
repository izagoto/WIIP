import os
import shutil
import hashlib
import json
import base64
import zipfile
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import UploadFile
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

from app.core.config import settings
from app.models.case_management import Evidence, ChainOfCustody, Case

class EvidenceService:
    def __init__(self, db: Session):
        self.db = db

    def calculate_file_hashes(self, file_path: str):
        """Calculates MD5 and SHA-256 hashes for a given file."""
        md5_hash = hashlib.md5()
        sha256_hash = hashlib.sha256()
        
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                md5_hash.update(chunk)
                sha256_hash.update(chunk)
                
        return md5_hash.hexdigest(), sha256_hash.hexdigest()

    def secure_wipe(self, file_path: str):
        """Overwrites the file with random bytes before deleting it."""
        if not os.path.exists(file_path):
            return
        
        file_size = os.path.getsize(file_path)
        with open(file_path, "wb") as f:
            # Overwrite with random bytes
            chunk_size = 65536
            for _ in range(0, file_size, chunk_size):
                f.write(os.urandom(min(chunk_size, file_size - f.tell())))
        os.remove(file_path)

    def encrypt_and_package_sdp(self, original_file_path: str, output_sdp_path: str, metadata: dict) -> str:
        """
        Encrypts the file with AES-GCM and packages it into a ZIP (.sdp).
        Returns the base64 encoded AES key.
        """
        key = get_random_bytes(32) # AES-256
        cipher = AES.new(key, AES.MODE_GCM)
        
        enc_file_path = original_file_path + ".enc"
        
        # Encrypt the file chunk by chunk
        with open(original_file_path, "rb") as f_in, open(enc_file_path, "wb") as f_out:
            while True:
                chunk = f_in.read(65536)
                if len(chunk) == 0:
                    break
                ciphertext = cipher.encrypt(chunk)
                f_out.write(ciphertext)
                
        tag = cipher.digest()
        nonce = cipher.nonce
        
        # Update metadata with cryptographic info
        metadata["encryption_algo"] = "AES-256-GCM"
        metadata["nonce"] = base64.b64encode(nonce).decode('utf-8')
        metadata["tag"] = base64.b64encode(tag).decode('utf-8')
        
        metadata_path = original_file_path + "_metadata.json"
        with open(metadata_path, "w") as m_out:
            json.dump(metadata, m_out, indent=2)
            
        # Create ZIP (.sdp) package
        with zipfile.ZipFile(output_sdp_path, 'w', zipfile.ZIP_DEFLATED) as sdp_zip:
            sdp_zip.write(enc_file_path, "data.enc")
            sdp_zip.write(metadata_path, "metadata.json")
            
        # Secure wipe temp files so original plaintext doesn't exist on disk
        self.secure_wipe(original_file_path)
        self.secure_wipe(enc_file_path)
        os.remove(metadata_path)
        
        return base64.b64encode(key).decode('utf-8')

    def ingest_evidence(self, case_id: int, file: UploadFile | None, source_type: str, investigator_id: int, file_path_override: str | None = None, filename_override: str | None = None) -> Evidence:
        """
        Ingests a new evidence file, calculates hashes, encrypts to .sdp, 
        securely wipes the original, and creates DB records.
        """
        # Ensure case exists
        case = self.db.query(Case).filter(Case.id == case_id).first()
        if not case:
            raise ValueError(f"Case with ID {case_id} not found.")

        # Prepare storage directory
        base_dir = os.path.join(os.getcwd(), settings.EVIDENCE_STORAGE_PATH)
        case_dir = os.path.join(base_dir, f"case_{case_id}")
        os.makedirs(case_dir, exist_ok=True)

        filename = filename_override or (file.filename if file is not None else "unknown_evidence")
        temp_file_path = os.path.join(case_dir, f"temp_{filename}")
        sdp_filename = f"{filename}.sdp"
        sdp_file_path = os.path.join(case_dir, sdp_filename)
        
        # Save uploaded file to disk temporarily
        if file_path_override:
            shutil.copyfile(file_path_override, temp_file_path)
            os.remove(file_path_override)
        elif file is not None:
            file.file.seek(0)
            with open(temp_file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        else:
            raise ValueError("Either file or file_path_override must be provided.")

        # Calculate original file hashes & size for Chain of Custody
        md5_hex, sha256_hex = self.calculate_file_hashes(temp_file_path)
        original_file_size = os.path.getsize(temp_file_path)
        
        metadata = {
            "original_filename": filename,
            "content_type": file.content_type if file is not None else "application/octet-stream",
            "original_size": original_file_size,
            "original_sha256": sha256_hex,
            "ingested_at": datetime.now(timezone.utc).isoformat()
        }

        # Auto-encrypt and package to SDP (original file gets wiped here)
        b64_key = self.encrypt_and_package_sdp(temp_file_path, sdp_file_path, metadata)
        
        # Get final SDP size
        final_file_size = os.path.getsize(sdp_file_path)

        # Create Evidence record
        evidence = Evidence(
            case_id=case_id,
            source_type=source_type,
            file_path=sdp_file_path,
            file_size=final_file_size,
            file_hash=sha256_hex,  # We store original hash for integrity verification
            md5_hash=md5_hex,
            file_metadata=json.dumps(metadata),
            status="processed",
            is_encrypted=1,
            encryption_key=b64_key
        )
        self.db.add(evidence)
        self.db.commit()
        self.db.refresh(evidence)

        # Create ChainOfCustody record
        coc = ChainOfCustody(
            evidence_id=evidence.id,
            investigator_id=investigator_id,
            action="imported_and_encrypted",
            notes=f"Evidence {filename} ingested, hashed (SHA256: {sha256_hex}), encrypted to SDP, and securely wiped."
        )
        self.db.add(coc)
        self.db.commit()

        return evidence
