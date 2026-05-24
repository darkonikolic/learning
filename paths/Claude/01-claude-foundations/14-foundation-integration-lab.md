# Foundations integration lab

**Purpose:** rehearse foundational moves **together** — Claude Code product literacy (`02`–`05`), context + token stewardship, layered five-block prompting, **SPEC on disk**, **CLAUDE.md / rules / skills / permissions** as hardened defaults.

**Prerequisites:** labs in `02`–`05` and at least `09` + `12` once. For multi-phase work next, continue with `15`–`18`.

Numerical prefixes = study ordering only.

---

## System snapshot card template (overwrite with truthful stack)

```
Symfony HTTP API boundary -> Go processing worker fleet -> authoritative MySQL
-> RabbitMQ retry / DLQ story -> Compose dev fidelity -> observability /
  on-call escalation hooks
```

---

## Model output cascade (**OUTPUT FORMAT** every time)

1. **Executive plan** — systems changing + why risky.  
2. **SPEC** — acceptance criteria split from noise (**from `docs/specs/` when feature-sized**).  
3. **Architectural schematic** — concurrency + duplicate-processing hazards.  
4. **Operationalized steps** — owners per step.  
5. **Trade-offs** — lean vs hardened paths.

---

## One-pass playbook

| Step | Activity |
|------|----------|
| 0 | Truthful system snapshot card. |
| 1 | `/context` — note memory + MCP footprint (`02`). |
| 2 | Confirm CLAUDE.md + `.claude/settings.json` current (`03`, `12`). |
| 3 | **`docs/specs/<slug>.md`** with ≥5 acceptance **or** plan in `docs/plans/` (`04`, `05`). |
| 4 | First message = five blocks (`08`) + card + scoped question; SPEC block matches on-disk file. |
| 5 | Execute bounded steps; `/diff` before done. |
| 6 | Tick acceptance in SPEC; capture config debt (`09`–`13`). |
| 7 | Metric grid below. |

---

## Minimum measurement grid

| Measure | Insight |
|---------|---------|
| Draft senior-accept threshold | qualitative bar |
| Correction rounds | iterative overhead |
| `/context` before/after | memory discipline |
| Permission prompts | governance tuning need |
| Context resets (`/compact`, `/clear`) | plan/SPEC-on-disk habit |
| Acceptance items verified | spec-driven discipline |

---

## Post-run journal

- what landed first-shot  
- forgotten **CONTEXT / CONSTRAINT**  
- wrong **slash command or mode** (`02`)  
- plan-only when SPEC was required (`05`)  
- config debt: CLAUDE.md, `.claude/rules/`, skill, MCP, permissions (`09`–`13`)

---

## Common pitfalls

- Plan only in chat → `/compact` → lost contract (`04`, `05`).  
- SPEC block in prompt **contradicts** `docs/specs/` file.  
- Long procedures in CLAUDE.md instead of skills (`10`, `12`).  
- Safety only in prose — no **deny** rules (`13`).  
- Huge paste in CONTEXT — see `06`, `07`.

---

## Next step — GSD capstone

Multi-phase work with `.planning/` → **`18-gsd-integration-lab.md`** (after `15`–`17`).

---

**Maintainability:** verify [Claude Code docs](https://code.claude.com/docs/en/overview) when paths or commands drift; refresh this unit accordingly.
