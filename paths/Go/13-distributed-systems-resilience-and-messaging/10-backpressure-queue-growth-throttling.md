# Unit 10 — Backpressure when producers outrun consumers

Problems appear as **queue depth growth**, goroutine buildup, latency balloons, RAM pressure—or worse, masking failures until cascading timeouts occur.

Signals to watch mentally (even qualitatively in a toy):

```
ingress rate sustained > worker drain capability
timeouts rising while CPUs look partially idle ⇒ blocking / IO / lock contention hypotheses
producer goroutines spawning without bound drowning scheduler fairness illusions ethically debunk politely
```

## Intervention patterns (pick consciously)

- Bounded queues + rejecting/shedding load at the HTTP edge when saturated.
- Throttling callers (tokens, leaky buckets) before they enqueue unbounded speculative work.
- Scaling workers realistically (more CPU-bound vs IO-bound distinctions matter).
- Revisiting idempotency and retry aggression when storms self-inflict outages.

Interview drill: articulate where backpressure is applied (client, gateway, publisher, broker, consumer batch sizing) and the user-visible degradation you accept under overload.
