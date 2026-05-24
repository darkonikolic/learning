# Unit 2 — Labs: AZ & region tabletops + CDN degrade

Diagram **A** (`baseline`): CDN → load balancer → app → cache/service bus → Postgres. Mark public vs private network bands.

Exercise **AZ loss**: annotate components that degrade vs stop; cite load balancer / readiness behaviour.

Exercise **CDN misconfig**: stale assets vs origin overload—state fallback policy.

Exercise **Regional DR tabletop**: state qualitative **RPO/RTO**, what data replication style you assume (async vs synchronous), and the cost/operational honesty of failing over—for your product tier, not hypothetical hyperscaler theatre.
