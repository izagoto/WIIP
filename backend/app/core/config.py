import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    PROJECT_NAME: str = "WIIP"
    # Provide a fallback just in case
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./wiip_dev.db")
    EVIDENCE_STORAGE_PATH: str = os.getenv("EVIDENCE_STORAGE_PATH", "data/raw_evidence")

settings = Settings()
