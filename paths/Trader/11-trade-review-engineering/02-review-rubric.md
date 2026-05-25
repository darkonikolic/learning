# Review rubric — grading trades and sessions

> Grade process first, outcome second. A clean loss is better data than a sloppy win.

---

## Trade grade matrix

Grade each trade on four dimensions. Overall grade = lowest single dimension grade.

### Dimension 1 — Thesis quality

| Grade | Criteria |
|---|---|
| A | Premise clearly stated pre-trade, matched playbook, falsifiers defined |
| B | Premise present but vague OR falsifiers missing |
| C | Entered without written hypothesis OR premise retroactively invented |

### Dimension 2 — Execution adherence

| Grade | Criteria |
|---|---|
| A | Entry, size, stop, exit all matched plan. Any deviation was pre-defined contingency |
| B | One minor deviation (e.g. limit missed by 1–2 ticks, partial size slightly off) |
| C | Stop moved, size deviated significantly, exit improvised, abort condition ignored |

### Dimension 3 — Risk conformance

| Grade | Criteria |
|---|---|
| A | Risk ≤ planned R, stop placement per risk sheet rules |
| B | Risk slightly above plan (≤ 1.5× planned) with documented reason |
| C | Risk exceeded plan without documented justification OR circuit breaker violated |

### Dimension 4 — Outcome (informational only — does NOT override process grade)

| Grade | Criteria |
|---|---|
| A | Met or exceeded planned target |
| B | Partial, broke even, or small loss with plan followed |
| C | Loss exceeded max R OR win achieved via violation (lucky break) |

---

## Overall trade grade assignment

**A trade** = all four dimensions A, or three A + one B  
**B trade** = mix of A/B — sloppy win or clean loss — both valid B  
**C trade** = any single C dimension — escalation required

---

## Example graded trade

**Trade:** EURUSD long, 2026-03-12

| Dimension | Grade | Notes |
|---|---|---|
| Thesis quality | A | Hypothesis written, invalidation defined pre-trade |
| Execution adherence | A | Entry within 1 pip of plan, partial exits hit targets |
| Risk conformance | A | 1% risk, stop per risk sheet |
| Outcome | A | +2.4R |

**Overall: A**

---

**Trade:** GBPUSD long, 2026-03-14

| Dimension | Grade | Notes |
|---|---|---|
| Thesis quality | B | Premise written but no invalidation level noted |
| Execution adherence | C | Stop moved 15 pips wider when trade went against — "gave it room" |
| Risk conformance | C | Effective risk became 2.1R due to stop move |
| Outcome | B | Ended at breakeven |

**Overall: C** ← execution and risk both C — triggers escalation review

---

## Weekly session review template

Run every Friday (or end of trading week):

```
Week of: ________
Total trades: ________
Grade distribution: A: __  B: __  C: __
Adherence ratio:    ___/___

Top mistake this week (tag):  ________
Root cause:                   ________
Backlog item created:         [ ] Yes → ________  [ ] No

Best process moment this week (what to repeat):
________

Playbook adjustment needed:  [ ] Yes → schedule cold review  [ ] No
```

---

## Monthly mistake leaderboard

Pick the top three recurring tags. Address exactly those three — not everything.

| Rank | Mistake tag | Count this month | Action |
|---|---|---|---|
| 1 | ________ | ________ | ________ |
| 2 | ________ | ________ | ________ |
| 3 | ________ | ________ | ________ |

---

## Escalation ladder

| Trigger | Action |
|---|---|
| 1 C-grade trade | Log root cause, no other action |
| 2 C-grade trades same week | Mandatory review before next session |
| 3 C-grade trades same week | Pause live trading, replay-only for ________ days |
| Same mistake tag 3× in one month | Playbook freeze — rewrite that rule before resuming |
| C on risk conformance + C on execution same trade | Senior review: am I in tilt loop? |
