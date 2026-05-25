# Pattern: Architecture and Design Decisions

```
Given: <current state — what exists now, what constraints are fixed>.
Problem: <specific issue — why the current state is insufficient>.
Propose 2-3 options.
For each option:
  - Name
  - Implementation sketch (not full code — key types, key interactions)
  - Pros (concrete, not "simpler")
  - Cons (concrete, not "more complex")
  - Risks (what can go wrong at scale or under change)
  - What it forecloses (what future changes become harder or impossible)
Do not recommend.
I will decide.
```

---

## Why the template is shaped this way

**"Do not recommend."**
When the model recommends, it anchors the decision. You read Option A (recommended) first, and Options B and C are evaluated against it. Your decision is no longer independent — it is a reaction. Architecture decisions have long tails; you need to own the choice without an anchor.

**"I will decide."**
Signals that the model's job ends at analysis. Without this, the model often appends a recommendation anyway, framed as "summary" or "my take." Explicit instruction stops it.

**Implementation sketch, not full code.**
You need enough structure to evaluate feasibility — key types, key interactions, which packages or interfaces are involved. Full code at this stage means you are already committed to an option before deciding. The sketch reveals tradeoffs without locking you in.

**"What it forecloses."**
This is the most important field and the most often omitted. Every architecture decision eliminates future options. A mutex-based store forecloses concurrent streaming updates without a rewrite. A channel-based store forecloses synchronous batch operations without coordination overhead. These foreclosures are often invisible until you hit them.

**"Concrete, not 'simpler'."**
"Simpler" is not a pro. "No lock contention under single-writer workload" is a pro. "Requires serializing all writes through a goroutine, adding latency to synchronous call paths" is a con. Force specificity.

---

## Filled Example

Choosing a concurrency strategy for the task-api in-memory store.

```
Given:
- task-api is a Go HTTP service with an in-memory task store.
- Handlers run in separate goroutines per request (net/http default).
- Current store is a plain map with no synchronization — data races confirmed under load.

Problem:
- Concurrent reads and writes to the map cause data races.
- Need a synchronization strategy before adding more endpoints.

Propose 2-3 options.
For each option:
  - Name
  - Implementation sketch (key types, key interactions — not full code)
  - Pros (concrete)
  - Cons (concrete)
  - Risks (at scale or under change)
  - What it forecloses

Do not recommend.
I will decide.
```

Expected output: three options such as (1) `sync.RWMutex` on the store struct, (2) channel-based serialization with a goroutine owning the map, (3) `sync.Map`. Each with concrete sketch and filled fields.

---

## What to Reject

| Signal | Why it's wrong |
|---|---|
| Single option presented as "the best approach" | Anchors decision; no alternatives to evaluate |
| "I recommend Option 2" anywhere in the output | Violates "do not recommend"; request output without the recommendation |
| Pros/cons that say "simpler" or "more complex" without specifics | Not evaluable; ask for concrete rewording |
| No "what it forecloses" field | Missing the most important field; request completion |
| Full implementation code provided | Premature commitment; replace with a sketch |
| Options that are not genuinely different tradeoffs | e.g., mutex variant A vs. mutex variant B; ask for a structurally different option |

---

## Checklist

- [ ] GIVEN section describes current state with specific constraints (language, existing structure, fixed dependencies)
- [ ] PROBLEM is a specific issue, not a vague concern
- [ ] Prompt asks for 2-3 options — not 1, not 5
- [ ] Each option includes: name, sketch, pros, cons, risks, what it forecloses
- [ ] Prompt explicitly says "do not recommend"
- [ ] Prompt explicitly says "I will decide"
- [ ] After output: each option has a concrete implementation sketch
- [ ] After output: pros and cons are specific, not adjective-based
- [ ] After output: "what it forecloses" is filled for each option
- [ ] Decision made independently, recorded in an ADR or spec before implementation begins
