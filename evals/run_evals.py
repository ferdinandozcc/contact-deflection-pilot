"""Scores the agent on the dev set (gates CI) and the held-out set (reported).

Metrics
- correct resolution: the agent answered and cited the right policy. This is real deflection.
- unsafe deflection: the agent answered a case a person should have taken. Gate: 0.
- wrong answer: the agent answered but cited the wrong policy. It looks deflected and comes back.
- unnecessary handoff: the agent sent to a person a case it could have answered. A cost, not a risk.
"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app.agent import handle

HERE = os.path.dirname(__file__)
GATE_MIN_CORRECT = 0.90   # dev set: correct decisions (right action and right policy)

def score(path):
    cases = json.load(open(os.path.join(HERE, path)))
    rows, m = [], dict(n=len(cases), intent=0, correct=0, resolved=0, correct_res=0,
                       unsafe=0, wrong_answer=0, unnecessary=0)
    for c in cases:
        r, e = handle(c), c["expected"]
        m["intent"] += r["intent"] == e["intent"]
        ok = r["action"] == e["action"] and (r["policy"] == e["policy"] or e["action"] == "handoff")
        m["correct"] += ok
        if r["action"] == "resolve":
            m["resolved"] += 1
            if e["action"] == "handoff": m["unsafe"] += 1; tag = "UNSAFE"
            elif r["policy"] != e["policy"]: m["wrong_answer"] += 1; tag = "wrong answer"
            else: m["correct_res"] += 1; tag = "ok"
        else:
            tag = "unnecessary handoff" if e["action"] == "resolve" else "ok"
            m["unnecessary"] += e["action"] == "resolve"
        rows.append((c["id"], c["text"][:60], f'{e["action"]}/{e["policy"]}', f'{r["action"]}/{r["policy"]}', tag))
    return m, rows

def pct(a, b): return f"{100*a/b:.0f}%" if b else "n/a"

def report(name, m, rows, out):
    n = m["n"]
    out.append(f"### {name} ({n} tickets)\n")
    out.append("| Metric | Value |\n|---|---|")
    out.append(f"| Intent accuracy | {pct(m['intent'], n)} |")
    out.append(f"| Correct decisions (action + policy) | {pct(m['correct'], n)} |")
    out.append(f"| Answered by the agent | {pct(m['resolved'], n)} |")
    out.append(f"| **Correctly resolved (real deflection)** | **{pct(m['correct_res'], n)}** |")
    out.append(f"| Wrong answers (will come back) | {m['wrong_answer']} |")
    out.append(f"| **Unsafe deflections** | **{m['unsafe']}** |")
    out.append(f"| Unnecessary handoffs | {m['unnecessary']} |\n")
    bad = [r for r in rows if r[4] != "ok"]
    if bad:
        out.append("| Ticket | Text | Expected | Got | Issue |\n|---|---|---|---|---|")
        out += [f"| {a} | {b} | {c} | {d} | {e} |" for a, b, c, d, e in bad]
        out.append("")

if __name__ == "__main__":
    mode = os.getenv("AGENT_MODE", "keywords")
    out = [f"## Deflection evals · understand() = {mode}\n"]
    dev, dev_rows = score("cases.json")
    hold, hold_rows = score("holdout.json")
    report("Dev set (gates the merge)", dev, dev_rows, out)
    report("Held-out set (never used for tuning)", hold, hold_rows, out)
    passed = dev["unsafe"] == 0 and dev["correct"] / dev["n"] >= GATE_MIN_CORRECT
    out.append(f"**Gate:** unsafe deflections = 0 and correct decisions ≥ {GATE_MIN_CORRECT:.0%} on the dev set → "
               + ("PASS" if passed else "FAIL"))
    text = "\n".join(out)
    print(text)
    if os.getenv("GITHUB_STEP_SUMMARY"):
        open(os.environ["GITHUB_STEP_SUMMARY"], "a").write(text + "\n")
    sys.exit(0 if passed else 1)
