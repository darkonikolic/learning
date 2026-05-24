# Claude workflow — from a question to a problem that produces an outcome

This unit defines your persistent **mindset**: **AI-assisted architect** with **Claude Code** (the goal is not “get text”; you steer **one concrete work problem**). **No calendar fiction** (“one fake week per topic”) — repeat the rituals as often as needed.

**Operational playbook:** `04-plan-to-execution-workflow.md`. **Specification habit:** `05-specification-before-implementation.md`. **Slash commands:** `02`. **Config map:** `03`. **Rules, skills, agents, memory, governance:** `09`–`13`. **GSD:** `15`–`18`.

Suggested early path: `02`–`05` → `09`–`13` → `15`–`17` → labs `14` then `18`.

## What changes if you internalize this

| Old habit | New habit |
|-----------|-----------|
| One question → polished story as the goal | One concrete **work problem** → **Claude workflow** → artefact/plan you can **check** against code or incident process |
| One giant prompt | Sessions where **you** decide what goes in next (**session ownership**) |
| Everything in my head → “implement now” | **Decomposition** stated in plain language first, **then** execution (**thinking vs execution**) |

## Procedure (sessions that matter for practice)

1. **Name the problem in one sentence** — not abstract (“explain DDD”) but grounded (“Our `Order` aggregate — cancel, refund, payment retry — I need a change plan against the code we run”).
2. **Break into 3–7 sub-steps** **in your own words** before you send anything to the model — required **thinking** slice.
3. **Give the model:**  
   - what you already know about the domain (short, factual),  
   - what is **out of scope** today,  
   - **exact output shape** (e.g. “steps first, then module boundaries, then risks”).
4. **Model proposes** — **you pick** what the next increment is; don’t spiral into vague “keep going”.
5. **Iterate from a flaw:** round two cites a **specific problem** (“no idempotency point at consumer edge”), not “do better”.

## Checklist before Send

- [ ] **One sentence:** what problem is today?
- [ ] **3–7 steps** written by **you** without copy/paste from the model  
- [ ] **Out-of-scope** called out explicitly  
- [ ] Desired artefact stated: **plan** | **SPEC** | **architecture** | **incident note** | **refactor plan**  

## Symfony drill

**Bad:** “build an order service”  

**Good:** “DDD `Order` aggregate. Rules: cancel, refund, payment retry. I need an **implementation plan** (bounds, use-case list, invariants, tests) — **no** full PHP in this round.”

## Go drill

Take one worker/queue scenario with **timeout** and **retry**. First ask for **flow sketch / components** plus where **idempotency** is missing — **then** code.

## Ops drill (Docker)

Enforce ordering:

1. **What logs say** (minimal, safe extract).  
2. **Hypotheses** (list).  
3. **Smallest experiment** probing one hypothesis (not “nuke reinstall everything”).  

## Mini-lab (your cadence — not calendar)

After a substantive session jot in private notes:

| Metric | Why |
|--------|-----|
| First-answer quality (1–5) | whether framing is precise enough |
| Iterations to acceptable artefact | whether **decomposition** needs work |
| How often **you** changed direction | **session ownership** signal |

## If you split “iteration tuning” later

Keep **guided iteration** over the **same task** for several tightening rounds as **its own subtopic sheet** later if helpful; basics already live above under iterative improvement.
