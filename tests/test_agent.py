"""Unit tests for the parts that decide money. These must never depend on the model."""
import json, types, sys
from app import agent
from app.agent import decide, guard

BASE = dict(deal_type="local", days_since_purchase=5, redeemed=False, appointment_booked=False,
            expired=False, final_sale=False, payment_valid=True, event_cancelled=False,
            days_since_delivery=None, prior_contacts=0)

def o(**k): return {**BASE, **k}

def test_cancel_inside_window_resolves():
    a, p, ans = decide("cancel_refund", [], o(days_since_purchase=14))
    assert (a, p) == ("resolve", "P-LOCAL-CANCEL") and "14-day" in ans

def test_cancel_outside_window_says_no_but_gives_next_step():
    a, p, ans = decide("cancel_refund", [], o(days_since_purchase=15))
    assert a == "resolve" and "passed" in ans and "still valid" in ans

def test_invalid_payment_method_goes_to_a_person():
    assert decide("cancel_refund", [], o(payment_valid=False))[0] == "handoff"

def test_legal_threat_always_escalates():
    assert guard({"intent": "cancel_refund", "confident": True, "flags": ["legal"]}, o()) == "ESC-LEGAL"

def test_repeat_contact_escalates_even_if_answerable():
    assert guard({"intent": "refund_status", "confident": True, "flags": []}, o(prior_contacts=2)) == "ESC-REPEAT"

def test_every_answer_has_a_next_step_or_handoff():
    cases = json.load(open("evals/cases.json"))
    for c in cases:
        r = agent.handle(c)
        assert r["answer"].strip(), c["id"]

def test_llm_output_is_validated(monkeypatch):
    class Msg:  content = [types.SimpleNamespace(text='sure! {"intent":"make_me_rich","confident":true,"flags":[]}')]
    class Client:
        def __init__(self): self.messages = types.SimpleNamespace(create=lambda **k: Msg())
    monkeypatch.setitem(sys.modules, "anthropic", types.SimpleNamespace(Anthropic=Client))
    out = agent.understand_llm("anything")
    assert out["intent"] == "other" and out["confident"] is False


def test_thinking_block_is_skipped(monkeypatch):
    class Msg:
        content = [types.SimpleNamespace(type="thinking", thinking="..."),
                   types.SimpleNamespace(type="text", text='{"intent":"find_voucher","confident":true,"flags":[]}')]
    class Client:
        def __init__(self): self.messages = types.SimpleNamespace(create=lambda **k: Msg())
    monkeypatch.setitem(sys.modules, "anthropic", types.SimpleNamespace(Anthropic=Client))
    assert agent.understand_llm("x")["intent"] == "find_voucher"

def test_api_error_becomes_handoff(monkeypatch):
    monkeypatch.setenv("AGENT_MODE", "llm")
    def boom(text): raise RuntimeError("api down")
    monkeypatch.setattr(agent, "understand_llm", boom)
    c = {"text": "refund please", "order": BASE}
    assert agent.handle(c)["action"] == "handoff"
