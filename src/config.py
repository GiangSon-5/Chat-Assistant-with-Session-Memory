import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

class Config:
    # LLM Settings
    LLM_API_BASE_URL = os.getenv("LLM_API_BASE_URL", "http://localhost:8000/v1")
    MODEL_NAME = "meta-llama/Meta-Llama-3-8B-Instruct"
    
    # Memory Settings
    # Default threshold (low for demo purposes, can be overridden)
    MEMORY_THRESHOLD_TOKENS = int(os.getenv("MEMORY_THRESHOLD_TOKENS", "1000")) 
    
    # Paths
    BASE_DIR = Path(__file__).resolve().parent.parent
    DATA_DIR = BASE_DIR / "data"
    SESSION_DIR = DATA_DIR / "sessions"
    TEST_DATA_DIR = BASE_DIR / "tests" / "test_data"

    @staticmethod
    def ensure_dirs():
        Config.SESSION_DIR.mkdir(parents=True, exist_ok=True)

Config.ensure_dirs()