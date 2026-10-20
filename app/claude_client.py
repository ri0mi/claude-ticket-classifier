import time 
from typing import Protocol 
from .models import LLMResult

SYSTEM = (
    "You classify customer emails. Reply ONLY with JSON: "
    '{"category": "billing|support|sales|other", '
    '"urgency": "low|medium|high", "summary": "<one sentence>"}'
)

class LLMClient(Protocol):
    def complete(self, user_text: str) -> LLMResult: ...

class FakeClient:
    """Devuelve respuestas predefinidas; si un elemento es una Exception, la lanza."""
    def __init__(self, responses: list | None = None):
        self.responses = list(responses or [])
        self.calls = 0

    def complete(self, user_text: str) -> LLMResult:
        self.calls += 1
        item = self.responses.pop(0) if self.responses else (
            '{"category":"support","urgency":"low","summary":"Fake summary"}'
        )
        if isinstance(item, Exception):
            raise item
        return LLMResult(text=item, input_tokens=len(user_text) // 4 + 40,
                         output_tokens=30, latency_ms=120)

class ClaudeClient:
    def __init__(self, model: str = "claude-haiku-5-5"):
        import anthropic
        self.client = anthropic.Anthropic()  # lee ANTHROPIC_API_KEY
        self.model = model

    def complete(self, user_text: str) -> LLMResult:
        t0 = time.perf_counter()
        r = self.client.messages.create(
            model=self.model, max_tokens=300, system=SYSTEM,
            messages=[{"role": "user", "content": user_text}],
        )
        return LLMResult(
            text=r.content[0].text,
            input_tokens=r.usage.input_tokens,
            output_tokens=r.usage.output_tokens,
            latency_ms=int((time.perf_counter() - t0) * 1000),
        )
