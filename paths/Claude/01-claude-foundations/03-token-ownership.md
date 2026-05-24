# Token ownership — never burn context unless it changes a decision

**Goal:** every message carries **only information that earns** the next architectural or technical decision — not “the whole universe” everywhere.

**No calendar fluff** — remeasure repeatedly on identical problems until instinctive.

## Principle

| Bad | Good |
|-----|------|
| Paste whole modules / monstrous inline diffs | Ship **precisely enough** prose + snippets to conclude **exactly one** decisive question |

## Symfony exercise path

Grab a **fat** bounded context/module you honestly know well.

**Round 1:** ask for critique with **everything** pasted (your definition of overstuffed attachments).  

**Round 2:** same question but **single aggregate (+ immediate interfaces coupling it)** input only.

**Round 3:** narrower still — **ownership boundary sketch** (“who talks to whom”) **or** one use case plus invariants exclusively.

### Measure each round

- guessed context weight (simple 1–3 scale works)  
- answer usefulness (self score 1–5)  
- wall-clock latency to actionable plan headline  

## Go mirror run

Triple input sweep over one backlog item:

1. entire `services` subtree dump  
2. only enqueue function body + immediate helpers  
3. retry policy excerpt + enqueue call snippet alone  

Journal which pairing **optimizes payoff vs pasted bytes**.

## Ops

Incident triage layering: symptom + **tiny** trustworthy log excerpt first → only then Compose/manifest excerpts when hypotheses demand them → never whole noisy cluster yarns unless hypotheses require them.

## Checklist before Send

- [ ] I can articulate **exactly one** pending architecture decision tied to prompt.  
- [ ] Deleted attachments that fail that decision hypothesis (old refactor notes, orphaned diffs).  
- [ ] Requested deterministic output shape (**decision bullets**, comparative table, phased steps).  

## Lab

Reuse one business-scoped issue three times altering only context sizing (table comparing **iteration × usefulness × pasted surface**).
