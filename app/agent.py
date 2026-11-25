"""Contact-deflection agent for Groupon-style support tickets.

Design rule: the model reads, the rules decide money.
  1. understand(): ticket text -> intent + risk flags. Keyword baseline offline,
     Claude when ANTHROPIC_API_KEY is set (AGENT_MODE=llm).
  2. guard():      flags + order history -> must a person take it?
  3. decide():     intent + order record -> policy, answer, next step.
Eligibility (refund yes/no) is never left to the model.
"""
import json, os, re

INTENTS = ["cancel_refund","expired_voucher","already_redeemed","merchant_refused","merchant_closed",
           "cant_book","appointment_change","goods_return","goods_faulty","refund_status",
           "live_event","find_voucher","fraud","complaint","other"]

# ---------- 1. understand ----------
KW = [
 ("fraud",            r"hack|didn'?t make|unauthori[sz]ed|not me|stolen account"),
 ("already_redeemed", r"(says|shows|marked)( as)? (redeemed|used)|shows .* as used"),
 ("merchant_refused", r"refuse|won'?t accept|not accept|don'?t take groupon|not valid"),
 ("merchant_closed",  r"closed|shut|out of business|nobody answers|no one answers|can'?t reach"),
 ("expired_voucher",  r"expired?"),
 ("goods_faulty",     r"broken|stopped working|faulty|defect|damaged"),
 ("goods_return",     r"send (them|it) back|return the|want to return|arrived"),
 ("refund_status",    r"where is my refund|not on my card|still (no|waiting).*refund|when will it arrive"),
 ("live_event",       r"concert|theatre|theater|show|ticket|gig|event"),
 ("appointment_change", r"move my|reschedul|cancel (tomorrow|today)'?s? appointment|second session|change .*appointment"),
 ("cant_book",        r"can'?t (find|get) .*(date|slot|book)|no availab|available dates"),
 ("find_voucher",     r"find my voucher|voucher code\?|can'?t see it"),
 ("cancel_refund",    r"refund|money back|cancel|changed my mind"),
 ("complaint",        r"nothing like|report you|terrible|disgust"),
]
FLAGS = {
 "legal":      r"chargeback|lawyer|solicitor|small claims|trading standards|\bcma\b|ombudsman|sue\b",
 "fraud":      r"hack|didn'?t make|unauthori[sz]ed",
 "vulnerable": r"passed away|died|funeral|bereave|hospital|cancer|emergency",
}

def understand_keywords(text):
    t = text.lower()
    hits = [name for name, rx in KW if re.search(rx, t)]
    flags = [f for f, rx in FLAGS.items() if re.search(rx, t)]
    # first match wins, but two strong, different intents = not confident
    strong = [h for h in hits if h not in ("cancel_refund","complaint")]
    intent = hits[0] if hits else "other"
    confident = bool(hits) and len(set(strong)) <= 1
    return {"intent": intent, "confident": confident, "flags": flags}

LLM_PROMPT = """You classify one customer-support message for a local-deals marketplace.
Return only JSON: {"intent": one of %s, "confident": true|false, "flags": subset of ["legal","fraud","vulnerable"]}.
confident=false if the message has no clear request or two different problems.
flags: legal = chargeback, lawyer, regulator or legal threat; fraud = account compromise or a purchase they didn't make;
vulnerable = bereavement, illness or emergency.
Message: <<<%s>>>"""

def understand_llm(text):
    import anthropic  # pip install anthropic
    client = anthropic.Anthropic()
    kw = dict(model=os.getenv("AGENT_MODEL", "claude-haiku-5-5"), max_tokens=2000,
              messages=[{"role": "user", "content": LLM_PROMPT % (INTENTS, text)}])
    try:   # a classification doesn't need extended thinking
        msg = client.messages.create(thinking={"type": "disabled"}, **kw)
    except TypeError:
        msg = client.messages.create(**kw)
    except Exception as e:
        if "thinking" not in str(e).lower(): raise
        msg = client.messages.create(**kw)
    # The response can start with a thinking block; read only the text blocks.
    raw = "".join(getattr(b, "text", "") for b in msg.content if getattr(b, "type", "text") == "text")
    if "{" not in raw:
        kinds = [getattr(b, "type", "?") for b in msg.content]
        raise ValueError(f"no JSON in reply (stop_reason={getattr(msg, 'stop_reason', '?')}, blocks={kinds}, text={raw[:80]!r})")
    out = json.loads(raw[raw.find("{"): raw.rfind("}")+1])
    if out.get("intent") not in INTENTS: out = {"intent":"other","confident":False,"flags":[]}
    out.setdefault("confident", False); out.setdefault("flags", [])
    return out

def understand(text):
    if os.getenv("AGENT_MODE") != "llm":
        return understand_keywords(text)
    try:
        return understand_llm(text)
    except Exception as e:  # bad JSON, API error, timeout: never answer on a broken read
        print(f"  [llm error -> handoff] {type(e).__name__}: {e}")
        return {"intent": "other", "confident": False, "flags": []}

# ---------- 2. guard ----------
def guard(u, order):
    if "legal" in u["flags"]:      return "ESC-LEGAL"
    if "fraud" in u["flags"] or u["intent"] == "fraud": return "ESC-FRAUD"
    if "vulnerable" in u["flags"] and u["intent"] != "expired_voucher": return "ESC-VULNERABLE"
    if order.get("prior_contacts", 0) >= 2: return "ESC-REPEAT"
    if not u["confident"] or u["intent"] == "other": return "ESC-LOWCONF"
    return None

# ---------- 3. decide ----------
def decide(intent, flags, o):
    """Returns (action, policy, answer). Answers always end with a next step."""
    H = "handoff"
    if intent == "cancel_refund":
        if not o["payment_valid"]:
            return H, "P-PAYMENT-CHANGED", "Your original card can't receive the refund, so a colleague will arrange where it goes."
        if o["redeemed"]:
            return "resolve", "P-LOCAL-CANCEL", "This voucher has been redeemed, so it can't be cancelled. If something went wrong at the merchant, reply and tell us what happened."
        if o["appointment_booked"]:
            return "resolve", "P-LOCAL-CANCEL", "You have an appointment booked. Cancel it first in My Groupons > See Details; then, if you're within 14 days of purchase, you can cancel the voucher there too."
        if o["days_since_purchase"] <= 14:
            return "resolve", "P-LOCAL-CANCEL", "You're within the 14-day cancellation window. Go to My Groupons > See Details > Cancel. The refund goes back to your original payment method; card refunds take 1–2 business days to process and up to 10 to show."
        return "resolve", "P-LOCAL-CANCEL", f"The 14-day cancellation window has passed ({o['days_since_purchase']} days since purchase), so this voucher isn't refundable, but it's still valid to use with the merchant until it expires."
    if intent == "expired_voucher":
        if "vulnerable" in flags:
            return H, "P-EXPIRED", "Because the voucher expired for reasons outside your control, a colleague will review your case. A refund isn't guaranteed, but we'll look at it properly."
        return "resolve", "P-EXPIRED", "Expired vouchers can't be redeemed and generally aren't refundable. If it expired because of exceptional circumstances, reply with what happened and we'll review it."
    if intent == "already_redeemed":
        return H, "P-ALREADY-REDEEMED", "A voucher marked redeemed that you didn't use needs a review; a colleague is taking it now."
    if intent == "merchant_refused":
        return H, "P-MERCHANT-REFUSED", "Your voucher is still valid, so we'll take this up with the merchant; a colleague is on it."
    if intent == "merchant_closed":
        return "resolve", "P-MERCHANT-CLOSED", "Sorry about that. Go to My Groupons > the order > See Details > Manage Voucher and choose the merchant-closed option; that opens a review with the order attached, so you won't need to explain it again."
    if intent == "cant_book":
        return "resolve", "P-CANT-BOOK", "Check the booking instructions on your voucher and pick dates inside the valid period. If there's still nothing available, use My Groupons > See Details > Manage Voucher to tell us."
    if intent == "appointment_change":
        return "resolve", "P-APPT-CHANGE", "You can change or cancel the appointment in My Groupons, usually up to 24–48 hours before it. For packages, you book one session at a time and the next opens once the previous one is done."
    if intent in ("goods_return","goods_faulty"):
        if intent == "goods_faulty":
            return "resolve", "P-GOODS-RETURN", "A faulty item can be returned under your statutory rights. Open My Stuff > the order and contact the seller to arrange it; the refund is processed 2–3 weeks after they receive the item."
        d = o.get("days_since_delivery") or 0
        if d <= 14:
            return "resolve", "P-GOODS-RETURN", "You're within 14 days of delivery. Open My Stuff > the order and contact the seller to cancel, then send it back within 14 days. The refund is processed 2–3 weeks after they receive it."
        return "resolve", "P-GOODS-RETURN", f"The 14-day return window has passed ({d} days since delivery). If the item is faulty, you still have a statutory right to return it; reply and tell us what's wrong."
    if intent == "refund_status":
        return "resolve", "P-REFUND-TIMING", "Card refunds are processed in 1–2 business days and can take up to 10 business days to appear on your statement. If it's not there after 10 business days, reply here and we'll trace it."
    if intent == "live_event":
        if o["event_cancelled"]:
            return "resolve", "P-LIVE", "Cancelled events are refunded. You'll see it in My Groupons; card refunds take up to 10 business days to appear."
        if not o["final_sale"] and o["days_since_purchase"] < 1:
            return "resolve", "P-LIVE", "You're within 24 hours of purchase, so you can cancel in My Groupons > See Details."
        return "resolve", "P-LIVE", "These tickets are Final Sale or past the 24-hour window, so they can't be refunded. If the organiser cancels or reschedules, you'll be refunded."
    if intent == "find_voucher":
        return "resolve", "P-FIND-VOUCHER", "Sign in and go to My Groupons on the website or app, then select the deal to see or print your voucher. If the deal has a future start date, the voucher appears once it starts."
    return H, "ESC-LOWCONF", "A colleague will pick this up."

def handle(ticket):
    u = understand(ticket["text"])
    o = ticket["order"]
    esc = guard(u, o)
    if esc:
        return {"intent": u["intent"], "action": "handoff", "policy": esc,
                "answer": "I'm passing this to a colleague with the details, so you won't need to repeat yourself."}
    action, policy, answer = decide(u["intent"], u["flags"], o)
    return {"intent": u["intent"], "action": action, "policy": policy, "answer": answer}
