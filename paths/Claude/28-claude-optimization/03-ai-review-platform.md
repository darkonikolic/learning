# AI review platform

**Theme:** Review is structured **verification of risk classes**—not passive reading.

### Dimensions every serious review Skill covers

Correctness vs acceptance / SPEC alignment  

Security-sensitive patterns surfacing blast radius shifts  

Maintainability & cognitive load—not only line count vanity  

Performance / scalability smell where SLO flagged  

Ownership / boundary integrity (Symfony DDD+CQRS, Go concurrency/error discipline)

### Authoring stubs (extend)

**Symfony review Skill** — aggregates vs integration edges, leaky services, CQRS inversion violations.  

**Go review Skill** — goroutine scopes, deadline propagation, typed error ownership, backoff sanity.  

**Ops review Skill** — Terraform blast, rollback readability, IAM least privilege regressions.

**LAB artefact**

`REVIEW_RUBRIC.md`: scoring tiers + mandatory blockers (“must escalate if rollback story absent”).

### Optimisation linkage

Higher **quality early** slashes downstream **repair** iterations—measure rubric conformance trend.

### Checklist

- [ ] Reviews log **severity + disposition** externally—not only inline chat fluff.  
