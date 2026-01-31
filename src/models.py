from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

# --- Chat Models ---
class Message(BaseModel):
    role: str
    content: str
    timestamp: Optional[str] = None

class ChatRequest(BaseModel):
    model: str
    messages: List[Message]
    temperature: float = 0.7
    max_tokens: int = 1024

# --- Feature A: Session Memory Schema ---
class UserProfile(BaseModel):
    preferences: List[str] = Field(default_factory=list)
    constraints: List[str] = Field(default_factory=list)

class SessionSummaryData(BaseModel):
    user_profile: UserProfile = Field(default_factory=UserProfile)
    key_facts: List[str] = Field(default_factory=list)
    decisions: List[str] = Field(default_factory=list)
    open_questions: List[str] = Field(default_factory=list)
    todos: List[str] = Field(default_factory=list)

class MessageRange(BaseModel):
    from_index: int
    to_index: int
    total_messages: int
    timestamp: str

class SummaryMetadata(BaseModel):
    summary_version: str = "1.0"
    tokens_saved: int
    compression_ratio: float

class SessionMemory(BaseModel):
    session_summary: SessionSummaryData
    message_range_summarized: MessageRange
    metadata: SummaryMetadata

# --- Feature B: Query Understanding Schema ---
class QueryAnalysis(BaseModel):
    """
    Kết quả phân tích câu hỏi. 
    Sử dụng Field(default...) để đảm bảo không bao giờ bị lỗi Validation.
    """
    original_query: str = Field(default="")
    is_ambiguous: bool = Field(default=False)
    ambiguity_reasons: List[str] = Field(default_factory=list)
    rewritten_query: str = Field(default="")
    needed_context_from_memory: List[str] = Field(default_factory=list, description="Keys from summary needed")
    augmented_context: str = Field(default="")
    clarifying_questions: List[str] = Field(default_factory=list)
    confidence_score: float = Field(default=0.0)
    requires_clarification: bool = Field(default=False)

    # Cấu hình để bỏ qua các trường thừa nếu LLM lỡ tay thêm vào
    class Config:
        extra = "ignore"