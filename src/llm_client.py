import requests
import json
import logging
import re
from typing import Dict, Any, List
from src.config import Config

logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self, base_url: str = Config.LLM_API_BASE_URL):
        self.base_url = base_url.rstrip("/")
        self.headers = {"Content-Type": "application/json"}

    def chat_completion(self, messages: List[Dict[str, str]], json_mode: bool = False) -> str:
        url = f"{self.base_url}/chat/completions"
        
        payload = {
            "model": "meta-llama/Meta-Llama-3-8B-Instruct",
            "messages": messages,
            "temperature": 0.1 if json_mode else 0.7, 
            "max_tokens": 2048
        }

        try:
            logger.info(f"Sending request to {url}")
            response = requests.post(url, headers=self.headers, json=payload, timeout=60)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"LLM API Call failed: {str(e)}")
            raise e

    def validate_json_output(self, content: str, pydantic_model: Any) -> Any:
        try:
            # 1. Loại bỏ lớp vỏ Markdown nếu có
            cleaned_text = content.replace("```json", "").replace("```", "").strip()

            # 2. Thuật toán tìm cặp ngoặc nhọn { } bao ngoài cùng
            start_index = cleaned_text.find('{')
            end_index = cleaned_text.rfind('}')

            if start_index != -1 and end_index != -1 and end_index > start_index:
                # Cắt lấy đúng phần JSON
                json_candidate = cleaned_text[start_index : end_index + 1]
                
                try:
                    # 3. Parse JSON sạch vào Pydantic Model
                    # Lúc này ta sẽ lấy được confidence_score: 0.8 gốc của AI
                    return pydantic_model.model_validate_json(json_candidate)
                except Exception as e:
                    logger.warning(f"Found {...} but content is invalid JSON: {e}")
                    # Nếu parse thất bại thì mới xuống Fallback
            else:
                logger.warning("No JSON brackets {...} found in response.")

            # --- FALLBACK  ---
            logger.warning("Active Fallback Mode due to parsing failure.")
            
            fallback_data = {
                "original_query": "Unknown",
                "is_ambiguous": True,
                "ambiguity_reasons": ["System Format Error"], 
                # Cắt ngắn text để tránh làm vỡ giao diện nếu text quá dài
                "rewritten_query": cleaned_text[:200], 
                "augmented_context": "Raw output could not be parsed.",
                "confidence_score": 0.1, # Điểm thấp báo hiệu lỗi hệ thống
                "requires_clarification": True
            }
            return pydantic_model.model_validate_json(json.dumps(fallback_data))

        except Exception as e:
            logger.error(f"FATAL ERROR parsing JSON: {e}")
            raise ValueError("Critical parsing error")