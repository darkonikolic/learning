# Service mesh thinking (conceptual)

**Theme:** **Traffic ownership abstraction** overlays retries, timeouts, telemetry, canary participation—without mandating immediate mesh adoption blindly.

Discuss pattern categories (ambient vs sidecar tradeoff mental model only—not vendor install recipes here):

**East–west traffic shaping** retries with **retry budget** scepticism distinguishing transient vs poison amplification  

Centralised observability enriching span continuity across Pod churn  

Fine-grained **failure injection rehearsal** philosophies (staging first) guarding cognitive overhead vs incident realism payoff

Resistance signals: latency tax, cryptographic overhead, blast radius converting previously simple TCP flows into chained policy evaluation—quantify sceptically rather than fetish upgrading.

Labs remain **design & critique** exercises referencing hypothetical mesh capabilities unless you purposely operate an installed mesh already.

### Checklist

- [ ] Document **explicit non-goals** when deferring mesh—what compensating primitives (Ingress timeouts, observability libs) compensate partially.  
