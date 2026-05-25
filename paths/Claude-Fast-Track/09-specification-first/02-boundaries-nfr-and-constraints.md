# Boundaries, NFR, and constraints

Three SPEC sections that developers routinely underspecify: Boundary / ownership, NFR, and Constraint. All three feel optional until you hit the failure mode they prevent. This file covers each in depth with task-api examples.

---

## Boundaries — who owns what

A boundary is a declaration of which module, package, or service is responsible for a decision. It is not an architecture diagram and not a class diagram. It is one sentence per ownership claim.

**Why boundaries in a SPEC matter:**

Without a boundary declaration, scope creep enters silently. "Just add the validation in the handler" is a five-second request that violates the domain layer's responsibility. When it happens during an execute session — and it will — Claude has no written rule to push back against. The boundary section is that rule.

**Boundary levels:**

| Context | Boundary unit | Example |
|---------|---------------|---------|
| Monolith | Package | `handler`, `domain`, `store` |
| Microservices | Service | `task-service`, `user-service` |
| GSD phases | Phase | Phase 1 owns task creation, Phase 2 owns task listing |
| DDD | Bounded context | `Order`, `Payment`, `Inventory` |

**Boundaries for task-api:**

The task-api has three packages. Each owns specific decisions. When a request crosses a boundary, it crosses via an explicit interface — not by one package importing another package's internals.

```
handler package
  - Owns: HTTP request parsing, HTTP response writing, status code selection
  - Does not own: business rule validation, data storage, Task struct definition

domain package
  - Owns: Task struct definition and field types, business rule validation
  - Does not own: HTTP concerns, storage concerns
  - Rule: validation logic lives here, not in handler

store package
  - Owns: in-memory state, task retrieval, task mutation
  - Does not own: validation, HTTP response format
  - Interface: List() []Task, Add(Task) Task, Complete(id string) (Task, error)
```

**Writing the boundary section:**

State what each participant owns and what it explicitly does not own. The "does not own" clause is as important as the ownership claim. It prevents encroachment.

Bad: "handler calls store"
Good: "handler owns HTTP parsing and delegates validation to domain; handler never implements validation logic inline"

---

## NFR — Non-Functional Requirements

NFRs define what "good enough" means for behavior that is not captured by functional acceptance criteria. An API that returns the right data in 30 seconds is not acceptable. An API that returns 200 but corrupts data on concurrent writes is not acceptable. NFRs are the specification for those quality dimensions.

**Categories with task-api examples:**

| Category | task-api example | Note |
|----------|-----------------|------|
| Latency | POST /tasks p99 < 10ms for up to 1000 concurrent requests | Hypothesis until benchmarked |
| Availability | 99.9% uptime during process lifetime | Inherited from infrastructure |
| Throughput | 500 requests/second sustained | Hypothesis until load tested |
| Data correctness | No task created twice from one POST request | Idempotency |
| Error format | All errors return `{"error": "..."}` JSON, never plain text | Consistency |
| Empty state | GET /tasks with no tasks returns 200 + `[]`, not 404 | Explicit behavior |

**Hypothesis vs measured — the required label:**

Every NFR that has not been tested is a hypothesis. Label it explicitly. This is not hedging — it is precision. A hypothesis is a target to measure against. An unlabeled number is a claim that may be wrong and will not be discovered until production.

```
# Marked correctly
Latency: p99 < 50ms for up to 100 tasks in memory (hypothesis — in-memory store, no benchmarks run)

# After benchmarking
Latency: p99 = 3ms (measured — go test -bench, 10k iterations, MacBook M2, 2024-01-15)
```

When you run the benchmark and record the result, update the SPEC. The SPEC is a living document for this. The label tells the next person whether to trust the number or to verify it.

**Minimum NFR set for any API feature, even toy projects:**

1. Latency target (even if hypothesis — forces you to think about the acceptable bound)
2. Empty state behavior (GET with no data: 200 + empty collection, not 404)
3. Error format consistency (all errors: same JSON shape)
4. Concurrent write safety (even "not applicable — single-threaded" is a valid answer)

Skipping these creates ambiguity. What does GET /tasks return when there are no tasks? If the SPEC doesn't say, Claude picks a default. The default may be wrong.

**NFR is not acceptance:**

NFRs are quality targets, not binary pass/fail for individual requests. A latency NFR of "p99 < 50ms" is satisfied if 99% of requests complete in under 50ms — not if one request takes 200ms. Do not put NFRs in the Acceptance section. Keep them separate so they can be measured separately.

---

## Constraints — hard rules

A constraint is a boolean rule: either satisfied or not. No measurement required. No threshold. Either the implementation uses stdlib only, or it does not.

**Constraints vs NFRs — the distinction:**

| | Constraint | NFR |
|--|------------|-----|
| Type | Boolean (violated or not) | Measurable (threshold) |
| Example | "must use stdlib only" | "p99 < 50ms" |
| Verification | Code review, import scan | Benchmark, load test |
| Partial compliance | No (binary) | Yes (degrees) |

**Types of constraints:**

**Must:** mandatory inclusions
- "must use Go 1.22+ slice.Contains"
- "must include request ID in every error response"

**Must not:** hard prohibitions
- "must not import external packages"
- "must not store task data outside the store package"
- "must not return 500 on client-caused errors"

**Stack rules:** technology restrictions
- "must use net/http stdlib router, not gorilla/mux or chi"
- "must not use init() functions"
- "must not use global variables"

**Why explicit constraints beat implicit:**

Claude picks defaults. Without a stdlib constraint, Claude may add `github.com/google/uuid` for UUID generation because it is more convenient than implementing UUID v4 using `crypto/rand`. Both approaches work. The constraint makes the choice non-negotiable.

The rule for authoring constraints: if you cannot determine with certainty whether a constraint is violated by reading the code, rewrite the constraint. "Keep dependencies minimal" is not a constraint — it requires judgment. "must not import packages outside the Go standard library" is a constraint — scan the import blocks.

**Constraints in task-api SPEC:**

```markdown
## Constraint
- Must use stdlib only (net/http, encoding/json, crypto/rand)
- Must not use goroutines in handler functions (store is not thread-safe)
- Must not return HTTP 500 for validation failures
- Must return JSON for all responses (no plain text, no HTML)
- Store must be injected via interface, not constructed inside handler
```

Each of these is verifiable by reading the code without running it.

---

## Cross-spec consistency

When multiple SPECs exist for the same system, they must agree on shared nouns. "Task" in `post-tasks.md` and "task" in `get-tasks.md` must have the same fields, types, and naming conventions. If POST /tasks returns `created_at` as an RFC3339 string and GET /tasks returns `createdAt` as a Unix timestamp, the API is inconsistent and the SPECs allowed it.

**The shared noun ledger:**

Maintain a brief document at `docs/specs/nouns.md` listing shared types when you have more than two SPECs:

```markdown
# Shared nouns

## Task
Fields: id (string, UUID v4), title (string), done (boolean), created_at (string, RFC3339)
Source of truth: domain.Task struct
Used in: post-tasks.md, get-tasks.md, complete-task.md
```

When a new SPEC needs to reference Task, it points to the ledger. If the Task struct changes, update the ledger and audit all SPECs that reference it.

**Consistency check before execute:**

Before running /gsd:execute-phase, if multiple SPECs are in scope, scan for noun divergence:
- Same field name across SPECs? (title vs task_title vs taskTitle)
- Same field type? (id as UUID vs id as integer)
- Same status code conventions? (201 Created for POST vs 200 OK)
- Same error format? (`{"error":"..."}` vs `{"message":"...","code":...}`)

One inconsistency found in SPEC is a five-minute fix. One inconsistency discovered in production is a breaking API change.

---

## Putting it together — complete NFR + Constraint + Boundary for GET /tasks

```markdown
## Boundary / ownership
- handler package: owns HTTP request parsing and JSON response writing
- store package: owns List() []Task — returns all tasks in insertion order
- domain package: owns Task struct; handler never re-declares field types
- handler must not call store directly by struct — must use store.TaskStore interface

## NFR
- Latency: p99 < 50ms for up to 100 tasks in memory (hypothesis — no benchmarks)
- Empty state: GET /tasks with 0 tasks returns 200 + [] (not 404, not null, not omitted)
- Error format: errors return {"error": "message"} JSON consistently
- Concurrent safety: not applicable — single-process, no concurrent writes in scope

## Constraint
- Must use stdlib only
- Must not return 404 for empty task list
- Must return Content-Type: application/json on all responses
- Must not implement pagination (out of scope)
- store.List() must return a non-nil empty slice, not nil, when no tasks exist
```

The last constraint on `store.List()` is precise. Without it, `json.Marshal(nil)` returns `null` instead of `[]`, and GET /tasks with no tasks returns `null` — which violates the NFR and may break client code.

---

## Checklist

- [ ] Boundary section names specific packages/modules and states what each owns and does not own
- [ ] Every NFR is labeled hypothesis or measured — no unlabeled numbers
- [ ] Minimum NFR set covered: latency, empty state, error format, concurrent safety (even if N/A)
- [ ] Constraints are boolean — each can be verified by reading the code
- [ ] No constraint contains "should", "try to", "minimize", "prefer" — those are preferences, not constraints
- [ ] Cross-spec noun consistency checked when multiple SPECs exist
- [ ] store.List() nil vs empty-slice distinction is explicit in constraint or NFR
