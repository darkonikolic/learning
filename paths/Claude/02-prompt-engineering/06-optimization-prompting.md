# Optimization prompting

**Theme:** Same outcome, **fewer iterations** and **less context burned** — this is where Phase 1 token ownership meets Phase 2 pattern choice.

## Decomposition first

Optimization is mostly **throwing away noise** once you’ve **decomposed** the real decision tree (same habit as the Phase 1 workflow / decomposition practice). Prompt v3 should still carry every constraint that moves the architectural outcome — shrink everything else.

## What “optimized” means here

You want the **same quality bar** with:

- fewer back-and-forth loops, and/or  
- smaller prompts (fewer tokens) without losing decision-critical facts.

## Practice — same problem, three prompt versions

Pick one scenario per stack (rotate):

| Track | Micro-scenario |
|-------|----------------|
| **PHP / Symfony** | One **aggregate** behavior change. |
| **Go** | One **worker** behavior (retry, DLQ, idempotency). |
| **Ops** | One **incident** triage write-up + next steps. |

Produce:

- **Prompt v1** — verbose, everything you “might” need.  
- **Prompt v2** — cut fat; keep constraints + spec + output format.  
- **Prompt v3** — minimal but still passes your quality checklist.

**Measure:** quality (same rubric), **iterations**, **tokens** (estimate if no meter).

## Checklist

- [ ] You did not delete **constraints** that change the answer.  
- [ ] Each version states the **same SPEC** so comparison is fair.  
