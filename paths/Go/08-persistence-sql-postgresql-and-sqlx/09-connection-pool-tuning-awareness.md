# Unit 9 — Connection pool configuration awareness (`database/sql` tuning mental hooks)

Tune cognitively—even if qualitative:

```
SetMaxOpenConns
SetMaxIdleConns
ConnMaxLifetime
```

Relate bursts of concurrent handlers + goroutines to pool starvation vs Postgres resource exhaustion interplay narrative—not numeric perfection yet.

Interview expectation: verbally distinguish misblaming DB vs mistaken pool undersizing hypotheses methodically narrowing production incidents hypothetical walkthrough style.
