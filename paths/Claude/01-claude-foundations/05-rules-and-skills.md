# Rules and Skills (Cursor)

**Goal:** encode recurring **ROLE / CONSTRAINT** fragments as persistent **Rules** (`AGENTS.md`, `.cursor/rules/*.mdc`, …) and **Skills** (`SKILL.md` where Cursor expects them). Session prompts stay terse because heavy policy already lives centrally.

Numerical prefixes = **concept order**, pretend calendar weeks **not** mandated.

## What’s what — current mental model (**verify against Cursor docs** when paths change)

- **Rules**: short evergreen guardrails (**always-ish** surfaced). Style, layering laws, autonomy limits.  
- **Skills**: procedural playbooks the agent may lazily hydrate when recognizing matching tasks — **provided** filenames + SKILL metadata advertise scenarios clearly according to Cursor’s current SKILL format (**double-check Cursor documentation** whenever something feels off).

Treat both as “stuff I historically re-pasted every session”; rewrite when product naming drifts (**flag outdated SKILL paths to the user**, don’t silently trust this sheet forever).

### Symfony policy seeds

- Modular DDD-ish boundaries consciously named  
- Explicit CQRS write/read separation expectations  
- No “utility sprawl burying domain decisions”  

### Go policy seeds

- Small cohesive interfaces; composition favored  
- Repos vs services vs transport handlers spelled per repo precedent  
- Dependency adds require justification snippets (e.g. agreed `database/sql`, `sqlx`, etc.)

### Ops policy seeds

- Incident docs: evidence → rollback knobs → timelines  
- Forbid “everything at once”; align with microscopic observability experiments identical to Ops drill elsewhere

**Skills complement rules** whenever a playbook would create unreadable RULE walls.

## Lightweight rule authoring skeleton

Draft **exactly**:

1. **Scope** directories / languages affected  
2. **Must / must-not** (**≤ five** razor statements)  
3. **Evidence format** reviewers expect (bullet diff plan, rollback recipe, comparative table…)  

Anything longer than a coffee skim will die unread.

### Skills mind-map (example profiles — invent real SKILL entries yourself)

| Persona-ish profile | Typical CONSTRAINT knobs |
|---------------------|------------------------|
| Go backend reviewer | concurrency, latency, package graph |
| Symfony architect | modules, aggregates, CQRS invariants |
| Ops debugger | hypotheses, blast-radius caps |

Author concrete `SKILL.md` bodies strictly per Cursor’s published instructions.

## Drill — before vs after codification

1. Pick grounded architecture ticket (replay-harden webhook, SLA bust, risky migration).  
2. **Baseline** prompt naked (no RULE/SKILL references).  
3. **Replay** attaching relevant Rules / Skills / workspace pointers (**same SPEC body** otherwise).  

Measure: minutes-to-usable-draft, regressions/backtracks, subjective prompt char count.

Notebook which noise classes evaporate thanks to layering.

## Checklist

- [ ] RULE length ≤ what a newcomer reads between meetings.  
- [ ] Must/must-not items machine-checkably binary (no fuzzy poetry).  
- [ ] Quarterly prune unused RULE noise / merge duplicated cousins.  
