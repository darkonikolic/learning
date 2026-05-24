# Unit 5 — `select`: multiplex channel readiness cleanly

## Learning outcome

Use **`select`** combining:

- progressing work readiness,
- **timeouts** driven by **`time.After`** idioms cautiously—or better integrate context cancellation next units holistically revisiting timeouts,
- **shutdown** signalling channel closed intentionally.

Understand pseudo-random fairness among simultaneous ready multi-case completions—avoid brittle ordering assumptions exploiting races.

## Practice

Unified worker loop juggling:

```
workCh
shutdownCh / done context
possibly watchdog timers
```

## Lab narrative obligation

Articulate consciously why naive **sleep-loop polling** corrodes readability + masks missed wakeups subtly.

## Interview prompts

Compose vs sequential channel reads patterns.

Dangerous **`default`** selects busy-spin regressions unintentionally resurrecting CPU waste.
