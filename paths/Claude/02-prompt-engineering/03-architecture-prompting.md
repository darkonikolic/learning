# Architecture prompting

**Theme:** Architecture work needs a **fixed skeleton** so every answer is comparable and reviewable.

## Template (six blocks)

Aligns with layered prompting; **RISKS** is explicit here because architecture without risk is fantasy.

1. **ROLE** — who signs off technically.  
2. **CONTEXT** — system truth slice (not a novel).  
3. **SPEC** — measurable outcomes / boundaries.  
4. **CONSTRAINTS** — stack + organizational rules.  
5. **RISKS** — what breaks, what scales badly, unknowns.  
6. **OUTPUT FORMAT** — diagram shape, headings, mandatory sections.

> **Overlap with Phase 1:** The foundations track uses five blocks (ROLE / CONTEXT / SPEC / CONSTRAINT / OUTPUT FORMAT). This unit adds **RISKS** as a first-class block for architecture-sized asks — merge them in practice.

## Practice rotations

| Track | Prompt shape |
|-------|----------------|
| **PHP / Symfony** | **DDD ecommerce** bounded contexts: commands/events, consistency boundaries. |
| **Go** | **Payment platform**: services, workers, idempotency, failure domains. |
| **Ops / IaC** | **Terraform (or IaC) architecture**: environments, modules, state, blast radius. |

## Lab — quality bar

The model output must visibly include:

- **Trade-offs** (at least two real alternatives).  
- **Risks** (technical + operational).  
- **Ownership** (who runs it, who changes it).  
- **Scaling** story (what breaks first under load or org growth).

**Measure:** how many **correction rounds** you need before those four show up cleanly.

## Checklist

- [ ] SPEC bullets are falsifiable without the model agreeing.  
- [ ] OUTPUT FORMAT demands **diagram + narrative**, not vibes.  
