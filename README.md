# Contact-deflection pilot (public-information exercise)

A small working pilot of an AI support agent for a local-deals marketplace. It answers what it can and hands the rest to a person. An eval measures both, and that eval gates every change in CI.

**Honest scope.** Policies come from Groupon's public UK/EMEA help centre and terms, checked 25 Nov 2026. Tickets are synthetic: I wrote them from common public complaint themes, and the order records are invented. The labels are my judgement. This is not Groupon's data, contact mix or internal policy, and it isn't affiliated with Groupon.

## The design rule: the model reads, the rules decide money

```
ticket ──► understand()  text → intent + risk flags      (Claude, or a keyword baseline offline)
       ──► guard()       legal · fraud · vulnerable · repeat contact · low confidence → person
       ──► decide()      intent + order record → policy ID + answer with a next step
```

Refund eligibility (windows, redeemed, appointment booked, final sale) is plain code over the order record, and unit tests cover it. The model is only trusted to read the message. Every answer cites a policy ID from `policies/policies.md`, and every answer ends with a next step.

## What the eval measures

| Metric | Why |
|---|---|
| Correctly resolved | Real deflection: the agent answered and cited the right policy. |
| Unsafe deflections | The agent answered something a person had to take. **Gate: 0.** |
| Wrong answers | Looks deflected, comes back later. A contact that returns wasn't deflected, it was postponed. |
| Unnecessary handoffs | A cost, not a risk. Tune these down only after unsafe is at 0. |

There are two sets:
- **Dev set** (36 tickets): this is what gates the merge.
- **Held-out set** (20 tickets): written after the rules were frozen and never used for tuning. Messier phrasing, typos, negations, plus Spanish and Italian.

## Result: keyword baseline

| | Dev set | Held-out set |
|---|---|---|
| Correct decisions | 100% | 35% |
| Correctly resolved (real deflection) | 61% | **5%** |
| Unsafe deflections | 0 | **1** |
| Wrong answers | 0 | 2 |
| Unnecessary handoffs | 0 | 10 |

The baseline passes its own gate perfectly and collapses on tickets it hasn't seen. The unsafe case is H04, "it's NOT expired", which a keyword rule reads as *expired*. A demo proves it works once; a held-out eval tells you whether it works.

## Result: Claude for `understand()` (v1, first run, 25 Nov 2026, claude-haiku-5-5)

| | Dev set | Held-out set |
|---|---|---|
| Correct decisions | 81% | 85% |
| Correctly resolved (real deflection) | 42% | **50%** |
| Unsafe deflections | **0** | **0** |
| Wrong answers | 3 | 2 |
| Unnecessary handoffs | 4 | 1 |

Real deflection on unseen tickets went from 5% to 50%, with no unsafe answers. **The gate still failed** (81% < 90% on dev), and correctly: the wrong answers weren't the model's. The customer asked for "a refund", the model read that right, and my rules applied the local-deal policy without checking that the order was a Live ticket or a hotel. The rules were supposed to own eligibility and ignored data the order already had. The model also flagged low confidence on messages that combine a request with context, which costs agent time but isn't a risk.

Next (v2): route by the order's deal type in `decide()`; clarify confidence in the prompt; write a fresh held-out set before measuring, because two held-out failures share the cause of the fix. One run only, so expect some variance.

To reproduce:

```
pip install -r requirements.txt
export ANTHROPIC_API_KEY=...
AGENT_MODE=llm python evals/run_evals.py
```

## Run it

```
python -m pytest -q                 # rules that decide money
python evals/run_evals.py           # evals; exit code 1 if the gate fails
```

CI (`.github/workflows/ci.yml`) runs the tests first, then the evals, and blocks the merge when the gate fails.

## Files

| Path | What |
|---|---|
| `policies/policies.md` | Policy base with IDs and public sources, plus my escalation rules |
| `app/agent.py` | understand → guard → decide |
| `evals/make_cases.py`, `evals/make_holdout.py` | Ticket generators (synthetic) |
| `evals/run_evals.py` | Scoring and the gate |
| `tests/test_agent.py` | Unit tests for eligibility, escalation and validation of model output |
