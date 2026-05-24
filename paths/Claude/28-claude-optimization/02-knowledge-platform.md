# Knowledge platform

**Theme:** Claude without curated knowledge scales **painfully**. Structure ownership so assistants pull **narrow, authoritative** bundles—not repo roulette.

### Illustrative tree (adapt paths)

```
 rules/
 skills/
 architecture/        ADRs + context maps
 incident/             postmortems + timelines
 runbook/               operational drills
 decision/             recorded tradeoffs (“why we rejected X”)
 spec/                  bounded artefacts per subdomain
```

### Domain hooks

**Symfony:** CQRS rules, **DDD / ownership** language, transactional boundaries surfaced in SPEC ids.  

**Go:** Retry doctrine, worker lifecycle narratives, concurrency context cheatsheets—**truth not folklore**.  

**Ops:** Rollback choreography, Terraform module contracts, escalation ladders.

### LAB

Produce **`KNOWLEDGE_OWNERSHIP_MAP`**: artefact folder → named human or role reviewer → freshness SLA → retrieval tag strategy.

Discuss **scalability**: more contributors demands **fewer handwritten long prompts**—more stable pointers retrievable on demand.

### Optimisation linkage

Shrinking noisy context boosts **speed** **and** **cost** **if accuracy** guarded—tie updates to KPI board from optimisation phase.

### Checklist

- [ ] Stale artefacts carry **SUPERSEDED** banners—prevent silent poisoning.  
