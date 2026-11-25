# Deflecting contacts without postponing them: a one-day pilot

**Ferdinando Zanardi · built on Groupon's public help centre · synthetic tickets, my labels**

## What I built
A support agent that answers what it can and hands the rest to a person, with an eval that gates every change in CI. Twelve public policies (local-deal cancellation, expired vouchers, redemption disputes, closed merchants, bookings, goods returns, Live tickets, refund timing). Five escalation rules. 56 synthetic tickets in English, Spanish and Italian.

## The one design choice that matters
**The model reads, the rules decide money.** The model only turns the message into an intent and risk flags. Whether a refund applies is plain code over the order record, with unit tests. Every answer cites a policy and ends with a next step. Legal threats, possible fraud, vulnerable customers, low confidence and **any second contact on the same order** go to a person: if the customer came back, the first answer didn't resolve it.

## What the eval showed (keyword baseline)

| | Dev set (gates CI) | Held-out set |
|---|---|---|
| Correctly resolved | 61% | **5%** |
| Unsafe deflections | 0 | **1** |
| Wrong answers (will come back) | 0 | 2 |

The baseline is perfect on the cases it was built with and fails on new wording. The unsafe case read "it's NOT expired" as *expired*. Three lessons:
1. **Gate on held-out, real tickets**, refreshed every month. A dev set you tuned against is a demo.
2. **Track deflection with resolution and repeat contact together.** "Answered" was 20% on held-out, but correct was only 5%.
3. **Language understanding is the model's job, eligibility isn't.** Spanish and Italian tickets defeated the keyword baseline completely.

## What I'd do first in a real stream
1. Pull about 300 real tickets from one stream, label intent and the correct outcome with agents, and hold out 100.
2. Start with informational intents that carry no money risk: refund timing, finding a voucher, changing a booking.
3. Never automate redemption disputes, merchant refusals or payment-method changes. Route them faster instead.
4. Ship behind a flag to a small share of traffic. Measure deflection, resolution and 7-day repeat contacts against a control.
5. Expand intent by intent, only while unsafe deflections stay at 0.

**With Claude reading the ticket (first run):** correctly resolved on held-out rose from 5% to **50%**, still **0 unsafe**. The gate still failed on dev, because my rules applied the local-deal policy to Live tickets and hotels without checking the deal type on the order. The gate caught a design flaw, not a model flaw.

*Limits: public policies, not internal ones; synthetic tickets and my labels; one run of the Claude version.*
