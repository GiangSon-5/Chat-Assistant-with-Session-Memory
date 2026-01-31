import logging
import json
from typing import List, Dict
from src.llm_client import LLMClient
from src.models import QueryAnalysis

logger = logging.getLogger(__name__)

class QueryProcessor:
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    def process_query(self, query: str, recent_history: List[Dict], memory_context: str) -> QueryAnalysis:
        logger.info(f"Processing query: {query}")
        
        history_text = json.dumps(recent_history[-5:], ensure_ascii=False) if recent_history else "[]"
        
        # --- CẬP NHẬT PROMPT VỚI RUBRIC CHẤM ĐIỂM ---
        system_prompt = """
        You are an expert Query Analyst for a RAG system.
        
        YOUR GOAL:
        1. Resolve pronouns (he, she, it, that) in the USER QUERY using CHAT HISTORY.
        2. Assign a 'confidence_score' based on the RUBRIC below.
        
        === SCORE RUBRIC (How to judge confidence) ===
        - 1.0 (Certain): The query names specific entities (e.g., "FastAPI", "PostgreSQL"). Or the context resolves 'it' uniquely without any doubt.
        - 0.8 (Likely): You inferred the target from context, but there is a small chance of error (e.g., user switched topics recently).
        - 0.5 (Unsure): The pronoun could refer to multiple things in history.
        - 0.1 (Guessing): No context available to resolve the ambiguity.

        EXAMPLE INPUT:
        History: [{"role": "user", "content": "I use Llama 3."}]
        Query: "Is it fast?"
        
        EXAMPLE OUTPUT (JSON):
        {
            "original_query": "Is it fast?",
            "is_ambiguous": true,
            "rewritten_query": "Is Llama 3 fast?",
            "confidence_score": 0.9, 
            "requires_clarification": false, 
            "ambiguity_reasons": ["'it' refers to Llama 3"],
            "needed_context_from_memory": [],
            "clarifying_questions": []
        }

        RESPONSE RULES:
        - Output STRICT JSON only.
        - ALL fields are required.
        - If 'confidence_score' < 0.9, you MUST set 'requires_clarification' to true.
        """

        user_prompt = f"""
        === LONG TERM MEMORY ===
        {memory_context}

        === CHAT HISTORY (Most Recent) ===
        {history_text}

        === CURRENT USER QUERY ===
        "{query}"
        
        OUTPUT JSON:
        """

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        try:
            raw_output = self.llm.chat_completion(messages, json_mode=True)
            analysis = self.llm.validate_json_output(raw_output, QueryAnalysis)
            
            # --- CÁC LOGIC  ---
            if not analysis.rewritten_query or not analysis.rewritten_query.strip():
                analysis.rewritten_query = query
            
            if not analysis.augmented_context or not analysis.augmented_context.strip():
                analysis.augmented_context = "No specific context resolved from history."

            if analysis.confidence_score == 0:
                analysis.confidence_score = 0.5 
                analysis.is_ambiguous = True
            
            return analysis

        except Exception as e:
            logger.error(f"❌ Query Analysis Error: {str(e)}")
            return QueryAnalysis(
                original_query=query,
                is_ambiguous=True,
                ambiguity_reasons=["System Processing Error"],
                rewritten_query=query,
                augmented_context="System error.",
                confidence_score=0.1,
                requires_clarification=True
            )