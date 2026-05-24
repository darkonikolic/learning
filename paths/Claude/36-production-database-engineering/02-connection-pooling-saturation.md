# Connection pooling & saturation ownership

**Theme:** Pools **hide** misconfiguration until blackout.

### Artefacts you should be able to reason about

- Max connections vs pods vs thread pools—**inventory inequality** maths.  

- Wait times & queue depths under burst (expose via metrics—not only pool counter).  

- Statement timeout interplay with HTTP/worker timeouts.  

- Credential rotation transient behaviour (sticky sessions vs pooled identity).

### LAB

Simulate contention in safe env; chart **latency vs saturation** crossover—document escalation before collapse.
