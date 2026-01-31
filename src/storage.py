import json
import logging
from pathlib import Path
from typing import Dict, List, Any
from src.config import Config

logger = logging.getLogger(__name__)

class StorageManager:
    @staticmethod
    def save_session_memory(session_id: str, memory_data: Dict[str, Any]):
        file_path = Config.SESSION_DIR / f"{session_id}_memory.json"
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(memory_data, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved memory for session {session_id}")
        except Exception as e:
            logger.error(f"Failed to save session memory: {e}")

    @staticmethod
    def load_session_memory(session_id: str) -> Dict[str, Any]:
        file_path = Config.SESSION_DIR / f"{session_id}_memory.json"
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load memory: {e}")
        return {}

    @staticmethod
    def load_test_data(filename: str) -> List[Dict]:
        path = Config.TEST_DATA_DIR / filename
        data = []
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        data.append(json.loads(line))
        return data