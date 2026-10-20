from app.claude_client import FakeClient
from app.processor import classify

def test_retries_on_bad_json():
    c = FakeClient(["not json", '{"category":"billing","urgency":"high","summary":"x"}'])
    ticket, _ = classify(c, "Me cobraron doble")
    assert ticket.category == "billing" and c.calls == 2

def test_retries_on_transient_error():
    c = FakeClient([RuntimeError("429"), '{"category":"sales","urgency":"low","summary":"x"}'])
    ticket, _ = classify(c, "Quiero una cotización")
    assert ticket.category == "sales"