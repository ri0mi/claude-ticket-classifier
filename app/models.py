from typing import Literal
from pydantic import BaseModel

class Ticket(BaseModel):
    category: Literal["billing", "support", "sales", "other"]
    urgency: Literal["low", "medium", "high"]
    summary: str

class LLMResult(BaseModel):
    text: str
    input_tokens: int
    output_tokens: int
    latency_ms: int    