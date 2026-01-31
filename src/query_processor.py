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
        
        # --- PROMPT: KẾT HỢP GIAO TIẾP + CODE INTENT ---
        system_prompt = """
        You are an expert Query Analyst for a RAG system.
        
        YOUR GOALS:
        1. Resolve pronouns (he, she, it, that) in the USER QUERY using CHAT HISTORY.
        2. Analyze if the query is Technical, Social, or Ambiguous.
        3. **CRITICAL:** If the query is about PROGRAMMING, IMPLEMENTATION, or "HOW TO", append "Please provide code examples" to the 'rewritten_query'.
        4. Assign a 'confidence_score' based on the RUBRIC below.
        
        === SCORE RUBRIC (How to judge confidence) ===
        - 1.0 (Certain): 
             a) The query names specific entities (e.g., "FastAPI", "PostgreSQL").
             b) OR The query asks for CODE/IMPLEMENTATION (e.g., "How do I write a loop?").
             c) OR The query is a CLEAR GREETING or SELF-INTRO (e.g., "Hi", "Hello", "My name is Son").
        - 0.8 (Likely): You inferred the target from context, but there is a small chance of error.
        - 0.5 (Unsure): The pronoun could refer to multiple things in history.
        - 0.1 (Guessing): No context available to resolve the ambiguity.

        === EXAMPLES FOR TRAINING ===

        -- Example 1: Coding Question (Add Code Request) --
        History: [{"role": "user", "content": "I want to build an API."}]
        Query: "How to start?"
        Output: {
            "original_query": "How to start?",
            "is_ambiguous": true,
            "rewritten_query": "How to start building an API? Please provide code examples.",
            "confidence_score": 0.9, 
            "requires_clarification": false, 
            "ambiguity_reasons": ["Inferred 'it' is API", "User wants implementation details"],
            "needed_context_from_memory": [],
            "clarifying_questions": []
        }

        -- Example 2: Social / Greeting (Keep Natural) --
        History: []
        Query: "Hi, my name is Son"
        Output: {
            "original_query": "Hi, my name is Son",
            "is_ambiguous": false,
            "rewritten_query": "Hi, my name is Son",
            "confidence_score": 1.0,
            "requires_clarification": false,
            "ambiguity_reasons": ["User is introducing themselves"],
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
            
            # --- CÁC LOGIC FALLBACK ---
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