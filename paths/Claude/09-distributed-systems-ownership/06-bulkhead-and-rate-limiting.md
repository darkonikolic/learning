# Bulkhead + rate limiting

**Theme:** **One sick dependency must not bankrupt every pool.** Isolate capacity; bound admission.

### Bulkhead intuition

Separate **executor pools**, **connection quotas**, logical tenant lanes—anything flammable gets a fence preventing total starvation of unrelated flows (“noisy neighbour” containment).

Discuss platform-native analogues versus app-level quotas (Kubernetes limits, proxy max connections)—your ownership layer matters.

### Rate limiting intuition

Admission control at edges (API gateways) plus **internal ingress** protecting downstream primitives (Redis, worker dispatch).

Token bucket vs leaky bucket vs concurrency slots—articulate fairness (per user / tenant / caller principal).

Overload responses: shed load predictably (`429`), prioritise monetised paths ethically if policy dictates.

### Checklist

- [ ] Burst vs sustained SLA codified—not only average RPS fantasies.  
