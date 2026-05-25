# Risk sheet — working template

> Print or pin next to workspace. Revise only in cold-state review, never mid-session.

---

## Account snapshot

| Field | Value |
|---|---|
| Total account value | ________ |
| Max risk per trade (% of account) | ________ % |
| Max risk per trade (cash) | ________ |
| Max simultaneous open risk | ________ % / ________ cash |
| Daily loss cap | ________ % / ________ cash |
| Weekly loss cap | ________ % / ________ cash |
| Drawdown from peak — throttle level | ________ % |
| Drawdown from peak — full stop level | ________ % |

---

## Position sizing formula

```
Units = (Account × Risk%) / (Stop distance × Multiplier)

Example (equities):
  Account = 10,000 EUR
  Risk per trade = 1% → 100 EUR
  Stop = 0.50 EUR per share
  Units = 100 / 0.50 = 200 shares

Example (FX, 1 pip = 0.10 EUR on 0.01 lot EURUSD):
  Account = 10,000 EUR
  Risk per trade = 1% → 100 EUR
  Stop = 20 pips
  Lot size = 100 / (20 × 10) = 0.50 lot

Slippage add-on: add 10–20% to stop distance in sizing calc for illiquid sessions.
```

Filled version (your instrument):
- Instrument: ________
- Contract multiplier / pip value: ________
- Typical stop range for my setups: ________ to ________
- Max units at max stop: ________

---

## Circuit breakers

| Trigger | Threshold | Action | Cooldown |
|---|---|---|---|
| Daily loss cap hit | ________ | Stop all trading | Until next session |
| Streak stop (N consecutive losses) | ________ losses | Stop, mandatory review | ________ hours |
| Drawdown throttle | ________ % from peak | Halve position sizes | Until equity recovers ________ % |
| Drawdown full stop | ________ % from peak | No live trading | Review + approval to resume |
| Tilt signal (see Psychology reset protocol) | subjective | Flatten open positions | 30 min minimum |

---

## Correlated exposure rule

Before adding a new position, check: does this share the same directional driver as anything already open?

Rule: max ________ positions sharing one macro driver simultaneously.

Example: long EURUSD + long GBPUSD + long gold = three USD-short bets. Treat as one correlated exposure block.

---

## Version control

| Version | Date | Change | Approved by |
|---|---|---|---|
| 1.0 | ________ | Initial build | ________ |
| | | | |

> Never change risk parameters during a losing streak. Schedule the next review date here: ________
