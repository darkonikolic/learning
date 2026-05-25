# Day in the life — full trading OS walkthrough

> One complete trading day, every artifact touched in sequence. This is the integration test of the system.

---

## The day at a glance

```
Pre-session (30–45 min)  →  Session open  →  Trade(s)  →  Session close  →  Evening review
```

---

## Pre-session protocol (30–45 min before market open)

**1. State check (2 min)**

Run tilt checklist from [Reset Protocol](../14-psychology-engineering/02-reset-protocol.md).

If 2+ checks: paper trade only today — note in journal.

**2. Context scan (10–15 min)**

Answer these questions before touching charts:
- What happened overnight? (one sentence)
- Any scheduled events today that trigger my news-freeze rule? Time: ________
- What is the general market tone? (risk-on / risk-off / choppy — one word)
- Is today a session I should be trading at all? (check session restrictions in playbook)

**3. Chart review — setup hunt (10–15 min)**

Go through your watchlist. For each instrument, ask:
- Is a setup from my playbook present or forming?
- What are the key levels I'll watch? (support, resistance, pivot)
- What would invalidate the setup before I even enter?

Write watchlist summary:
```
Instrument: ________  |  Setup forming: Yes / No  |  Key levels: ________
Instrument: ________  |  Setup forming: Yes / No  |  Key levels: ________
Instrument: ________  |  Setup forming: Yes / No  |  Key levels: ________
```

**4. Risk check (2 min)**

- Check current account equity: ________
- Are any circuit breakers already triggered from prior days? ________
- Today's available risk budget: ________ (account × max daily % - any open risk)
- Max position size today: ________ (reference [Risk Sheet](../04-risk-engineering/02-risk-sheet-template.md))

---

## During session — live trading

**Before each trade: fill pre-trade journal entry completely** (see [Journal Schema](../10-journaling-systems/02-journal-schema.md))

No exceptions. If no time to fill pre-trade fields — no trade.

**Trade execution sequence:**
1. Setup conditions confirmed (check against playbook checklist)
2. Anti-pattern check cleared
3. Pre-trade journal entry complete
4. Size calculated from risk sheet
5. Order placed — order type per execution playbook
6. Alerts set for: stop level, target 1, thesis invalidation level

**Intra-trade discipline:**
- Hands off unless material state change
- Do not check P&L in EUR/cash — only in R terms if at all
- If tilt signals emerge → Tier 1 reset immediately

---

## Session close protocol (15 min after last trade or at session end)

**1. Post-trade entries** (if not already done intraday)

Fill post-trade section for every trade today.

**2. Daily adherence log**
```
Trades today:          ________
A grades:  ___  B: ___  C: ___
Adherence ratio:       ___ / ___ trades followed plan
Circuit breaker used:  [ ] Yes → ________  [ ] No
Tilt reset activated:  [ ] Yes → ________  [ ] No
```

**3. Platform close**
- Export blotter / statement if broker allows — save to archive folder
- Screenshot any open positions if carrying overnight
- Close order entry panel

---

## Evening review (20–30 min, after dinner, not immediately after close)

Distance from session helps honest review. Do not do this immediately after a bad loss.

**Trade walkthrough:**

For each trade today, run through:
- Did the setup conditions exist as I thought? (Yes / No / Partly)
- Grade: A / B / C (use [Review Rubric](../11-trade-review-engineering/02-review-rubric.md))
- One sentence: what would I do the same? what would I change?

**Weekly tally update** (daily running count):

```
Week to date: A: __  B: __  C: __
Running adherence: ___/___
Mistake tag frequency this week: ________
```

**Backlog check:**

Did today surface a playbook ambiguity or recurring mistake?
- [ ] Yes → add to experiment backlog in relevant playbook
- [ ] No

**Tomorrow prep (2 min):**
- Anything to watch overnight?
- Any changes to watchlist?
- Any news events tomorrow that trigger freeze rules?

---

## Full artifact chain — one trade, all documents

A single trade should touch these documents. If any link is missing, the system has a gap.

```
[Risk Sheet v___]
    ↓ position sizing
[Playbook v___ — setup name]
    ↓ entry/exit/anti-pattern rules
[Journal — pre-trade entry]
    ↓ during trade
[Journal — intra-trade if material]
    ↓ after close
[Journal — post-trade entry]
    ↓ end of session
[Daily adherence log]
    ↓ evening review
[Trade grade — Review Rubric]
    ↓ if C grade
[Escalation ladder → Backlog / Tier reset]
    ↓ weekly
[Mistake leaderboard → Playbook patch proposal]
```

---

## System fragility check (run monthly)

List five things that could silently break this system without you noticing:

1. ________
2. ________
3. ________
4. ________
5. ________

For each: which document or rule covers it? If none: add to backlog.
