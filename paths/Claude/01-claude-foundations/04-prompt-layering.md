# Layered prompting — five blocks instead of “just do X for me”

**Goal:** non-trivial requests open with **five visible blocks** so the model inherits your org reality intentionally (see context + token hygiene units). Topics ordered by numbering here — never calendar weeks baked into filenames-as-schedule mythology.

## The five blocks

1. **ROLE** — persona who adjudicates architectural trade-offs (senior CQRS-owner for subsystem X?).  
2. **CONTEXT** — tight slice of truthful system circumstance (no lore dump).  
3. **SPEC** — bullet measurable outcomes reviewers can tick blindly.  
4. **CONSTRAINT** — bans + stack conventions the model cannot hand-wave past.  
5. **OUTPUT FORMAT** — deterministic shape readers expect (**ASCII diagrams, two-column deltas, enumerated steps**, etc.)

“Write me an API” alone forces invented constraints → usually wastes an entire conversational revolution.

## Small template (adapt names & stack)

```
ROLE: Senior Go engineer guarding internal payout webhooks; double application of monetary side-effects forbidden.

CONTEXT: HTTP intake, Rabbit worker fleet, upstream partners replay identical payloads.

SPEC:
- Retry strategy + rationale (fixed vs exponential).
- Exact DLQ hook + semantics for discarded poison messages.
- Field bundle forming idempotent processing key(s).
- Per-consumer SLA budget assumptions.

CONSTRAINT:
- Standard Go error ergonomics — no swallowed errors.
- New dependency ⇒ short human-readable trade-off blurb referencing alternatives.

OUTPUT FORMAT:
1. ASCII funnel HTTP -> worker -> retry -> DLQ
2. Two-column viability matrix (minimal vs resilient paths)
3. Invariants resilient to webhook replay bombardment
```

## Cross-stack rehearsal (reuse identical SPEC skeleton)

Reuse one architectural spine (replay-happy webhook). Swap **CONTEXT/CONSTRAINT** only:

| Stack | Twist |
|-------|-------|
| Symfony | CQRS/module boundaries spelled from your codebase |
| Go | Packages + concurrency expectations mirror actual modules |
| Ops | Incident triad: observable symptom → hypothesis → microscopic experiment probing one hypothesis |

## Practice spin (frequency up to you)

Queue small architecture riddles → **three prompts** each differing ONLY by CONTEXT granularity or CONSTRAINT strength → count conversational turns senior engineers deem acceptable vs noise.

## Checklist prior Send

- [ ] One declarative clause states **precise unlocking decision**.  
- [ ] Every SPEC line is objectively pass/fail without model collusion.  
- [ ] A teammate reading **OUTPUT FORMAT** alone anticipates eventual document skeleton.  
