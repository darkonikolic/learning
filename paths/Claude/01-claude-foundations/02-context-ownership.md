# Context ownership — what Claude actually “sees”

**Goal:** always remember Claude has **no magic access** — it sees **only what you supply**. **You own** context; the model consumes it efficiently when it is truthful and scoped.

**No calendar gimmicks** — practice until reflexively asking “what is actually on input right now?”

## Bad vs good mental model

| Bad (illusion) | Good (reality) |
|----------------|----------------|
| “Claude knows my whole repo” | Claude knows **messages + attachments + open editor context + Rules + Skills nothing else** unless you pasted it |
| Tiny prompt vs huge unknown system | Big problems deserve **layered deliberate** prompts (explicit **ROLE / CONTEXT / SPEC / CONSTRAINT / OUTPUT FORMAT** once you cross beyond one vague sentence) |

## Exercise: equally hard prompt, richer vs thinner input

### Task A — “small” prompt

**Example:** “Build retry for an HTTP client.”  

**Watch:** guesses about **missing** libs, semantics, infra.

### Task B — “fat” prompt (same domain intuition, sharper edges)

Example **Go-ish** briefing:

- RabbitMQ  
- who owns retries / queues  
- idempotency  
- DLQ  
- context timeouts  
- sync vs async handoff  

**Watch:** surprises shrink when borders are spelled out.

### Required comparison note (5–10 bullets after A & B)

- where A was fast but misleading architecturally  
- where B slowed reading yet matched real constraint surface  

## Symfony drill

Run the **same** architecture task twice:

1. **Without** spec (spoken intent only).  
2. **With** spec: CQRS/DDD fences you genuinely use (**boundaries**, **invariants**).  

Contrast first vs second response quality (whole chat logs optional).

## Lab — repeat freely

Pick one realistic task → **three** context shapes:

1. **Minimal** — one-sentence issue.  
2. **Healthy** — problem + fences + tiny relevant excerpt or ASCII sketch.  
3. **Huge** — “everything”: whole module bundles, backlog noise, stray files.

**Observe** where (1)-(2) best trade signal/cost tokens and where (3) adds noise only.

## Checklist

- [ ] I wrote down **everything the model absolutely did NOT see**.  
- [ ] Listed **explicit out-of-scope** guardrails.  
- [ ] There is exactly **one** snippet that earns its bytes — **not** “whole 200-file tree pasted”.  
