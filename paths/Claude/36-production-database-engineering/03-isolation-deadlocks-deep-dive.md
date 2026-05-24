# Transaction isolation & deadlock investigation deep dive

**Theme:** Locks are **engineering facts**, not DBA folklore.

### Isolation recap (actionable questions)

Which anomalies (dirty read / non-repeatable / phantom / skew) remain **accepted** vs **fatal** money risks for each query class?

### Deadlock anatomy

Practice reading deadlock graph excerpts: ordering inversions vs single hot row vs lock escalation class confusions—then choose **ordering discipline**, shorter transactions, or **optimistic** shift.

Deliverable snapshot: annotate one historical (or fabricated) deadlock with **preventive test** strategy.
