import time
from pydantic import ValidationError
from .models import Ticket, LLMResult

def classify(client, text: str, max_attempts: int = 3) -> tuple[Ticket, LLMResult]:
    prompt = text
    last_error = None
    for attempt in range(max_attempts):
        try:
            res = client.complete(prompt)
        except Exception as e:           # con la API real: RateLimitError, APIStatusError 5xx...
            last_error = e
            time.sleep(0.1 * 2 ** attempt)   # backoff exponencial
            continue
        try:
            return Ticket.model_validate_json(res.text), res
        except ValidationError as e:
            last_error = e
            prompt = f"{text}\n\nYour previous answer was invalid JSON/schema: {e}. Reply only with valid JSON."
    raise RuntimeError(f"failed after {max_attempts} attempts: {last_error}")