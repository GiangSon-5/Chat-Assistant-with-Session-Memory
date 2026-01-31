import logging
import json
from datetime import datetime # <--- Đảm bảo có dòng này
from typing import List, Dict, Optional
from src.models import SessionMemory, Message
from src.llm_client import LLMClient
from src.token_counter import TokenCounter
from src.storage import StorageManager

logger = logging.getLogger(__name__)

SUMMARY_SYSTEM_PROMPT = """
You are a Memory Manager AI. Your goal is to condense conversation history into a structured JSON summary.
Capture user profiles, key facts, decisions, open questions, and todos.
OUTPUT MUST BE VALID JSON ONLY. NO EXPLANATION.
Schema:
{
  "session_summary": {
    "user_profile": {"preferences": [], "constraints": []},
    "key_facts": [],
    "decisions": [],
    "open_questions": [],
    "todos": []
  },
  "message_range_summarized": {
    "from_index": <int>,
    "to_index": <int>,
    "total_messages": <int>,
    "timestamp": "<iso_str>"
  },
  "metadata": {
    "summary_version": "1.0",
    "tokens_saved": <int>,
    "compression_ratio": <float>
  }
}
"""

class SessionMemoryManager:
    def __init__(self, session_id: str, llm_client: LLMClient):
        self.session_id = session_id
        self.llm = llm_client
        self.token_counter = TokenCounter()
        self.current_memory: Optional[SessionMemory] = None
        self._load_memory()

    def _load_memory(self):
        data = StorageManager.load_session_memory(self.session_id)
        if data:
            self.current_memory = SessionMemory(**data)

    def check_and_summarize(self, messages: List[Dict], threshold: int) -> Optional[SessionMemory]:
        """
        Checks if context exceeds threshold. If so, triggers summarization.
        """
        current_tokens = self.token_counter.count_messages(messages)
        logger.info(f"Current context tokens: {current_tokens}/{threshold}")

        if current_tokens < threshold:
            return None

        logger.info("Threshold exceeded. Triggering summarization...")
        
        # Lấy thời gian thực để đưa vào Prompt
        current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Prepare prompt
        msgs_text = json.dumps(messages, ensure_ascii=False)
        
        # Prompt được cập nhật để chứa thời gian
        prompt_content = f"""
        Current Date & Time: {current_time_str}
        
        Summarize these messages into JSON:
        {msgs_text}
        """

        prompt_messages = [
            {"role": "system", "content": SUMMARY_SYSTEM_PROMPT},
            {"role": "user", "content": prompt_content}
        ]

        # Call LLM
        raw_output = self.llm.chat_completion(prompt_messages, json_mode=True)
        
        # Parse and Validate
        try:
            summary_obj = self.llm.validate_json_output(raw_output, SessionMemory)
            
            # Calculate stats
            tokens_after = self.token_counter.count_tokens(json.dumps(summary_obj.model_dump()))
            summary_obj.metadata.tokens_saved = current_tokens - tokens_after
            summary_obj.metadata.compression_ratio = round(tokens_after / current_tokens, 2)
            
            self.current_memory = summary_obj
            StorageManager.save_session_memory(self.session_id, summary_obj.model_dump())
            return summary_obj
        except Exception as e:
            logger.error(f"Summarization failed: {e}")
            return None

    def get_context_string(self) -> str:
        if not self.current_memory:
            return ""
        return json.dumps(self.current_memory.session_summary.model_dump(), indent=2, ensure_ascii=False)