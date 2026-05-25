# Journal schema — minimum viable, always honest

> Minimum schema you actually maintain beats ornate template abandoned in week two. Expand a field only when a specific analytic question is blocked without it.

---

## Pre-trade entry (fill before order is placed)

```
Date/time:         ________
Instrument:        ________
Playbook tag:      ________  ← must match exact setup name from playbook
Playbook version:  v________

HYPOTHESIS (what has to be true for this to work):
________

INVALIDATION (what would tell me I'm wrong, before stop hits):
________

PLANNED entry:     ________
PLANNED stop:      ________
PLANNED target(s): ________  /  ________
Planned risk (R):  ________
Planned R:R ratio: ________

Emotion tag (1–5):  1=calm  2=alert  3=elevated  4=anxious  5=impulsive
                    ________

Anti-pattern check: [ ] passed — no abort condition triggered
```

---

## Intra-trade entry (only if material state change)

```
Time:       ________
Event:      ________
Action:     ________
Reason:     ________
```

Resist logging every tick. Material = thesis changed, news hit, significant price action against plan.

---

## Post-trade entry (fill within 30 min of close)

```
Date/time closed:    ________
Actual entry:        ________
Actual stop hit:     ________  (or manual exit at ________)
Actual exit:         ________
Realised R:          ________
Realised P&L (EUR):  ________

ADHERENCE: Did execution match the pre-trade plan? [ ] Yes  [ ] No
  If no — deviation tag:
    [ ] Entry chased (entered outside trigger zone)
    [ ] Stop moved (widened or removed mid-trade)
    [ ] Size deviated (larger or smaller than risk sheet)
    [ ] Exit improvised (different from planned tiers)
    [ ] Abort condition ignored
    [ ] Other: ________

DEVIATION notes (what happened, not self-criticism):
________

POST-TRADE emotion tag (1–5): ________

SCREENSHOT: attached / not needed
```

---

## Review hook (daily)

At session end, complete these two lines:

```
Today's adherence ratio: ___/___  trades followed plan
Top pattern from today:  ________
Backlog item triggered:  [ ] Yes → ________  [ ] No
```

---

## Example entry (filled)

**Pre-trade**
```
Date/time:         2026-03-12  09:32
Instrument:        EURUSD
Playbook tag:      London-breakout-continuation
Playbook version:  v2.1

HYPOTHESIS: Price broke above 09:00 range with volume, retesting broken level,
            expecting continuation north to 1.0920 daily pivot.

INVALIDATION: Price closes 15min candle back inside range below 1.0878.

PLANNED entry:     1.0885 limit
PLANNED stop:      1.0872 (13 pips below range high)
PLANNED target(s): 1.0905 (partial) / 1.0920 (full)
Planned risk (R):  1% account = 100 EUR
Planned R:R ratio: 1:2.7

Emotion tag: 2 — alert, rested, no overnight stress

Anti-pattern check: [x] passed
```

**Post-trade**
```
Date/time closed:    09:58
Actual entry:        1.0886
Actual stop:         not hit
Actual exit:         1.0905 (partial 50%), 1.0918 (remainder, trailed)
Realised R:          +2.4R
Realised P&L:        +240 EUR

ADHERENCE: [x] Yes

POST-TRADE emotion tag: 2 — neutral, no euphoria
```

---

## Taxonomy maintenance

Setup tags in use (prevent synonym creep — audit monthly):

| Tag | Setup name | Active? |
|---|---|---|
| ________ | ________ | Yes |
| ________ | ________ | Yes |

Emotion anchor scale (calibrate your own — example):
- 1 = relaxed, focused, slept well
- 2 = alert, engaged, normal
- 3 = mildly tense, some background stress
- 4 = anxious, urgency present, want to trade
- 5 = impulsive, FOMO active, avoid live trading

> If emotion tag is 4 or 5 in pre-trade: paper trade only, or skip session.
