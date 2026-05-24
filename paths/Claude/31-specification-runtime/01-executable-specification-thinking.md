# Executable specification thinking — framing

## Phase framing — Specification Runtime (“Phase 11.7”)

**Units in this folder:** `01`–`05` (topic order only).

### Themes

**Executable spec** • **drift detection** • **spec consistency** • **acceptance ownership**

### Spine (every slice)

```
 SPEC (truth for this increment)
           → IMPLEMENTATION
                          → VERIFICATION (diff spec vs behaviour + acceptance)
                                                      → drift DETECT → REPAIR loop
```

**Checkpoint mantra:** Claude does not “ship code”—it implements a **frozen specification**, then **verifies itself** against that contract—including **constraints**, **NFRs**, **ownership**, and **acceptance criteria**.

Target stack rehearsals: **Symfony**, **Go**, **RabbitMQ**, **MySQL**, **Docker** Claude workflows—constraints must survive the whole toolchain.

---

### Executable spec — what “good” looks like

**Weak:** “Build a retry system.”  

**Strong:** Declared, checkable knobs, for example:

`retry.max_attempts = 3`  

`retry.per_attempt_timeout = 5s`  

`retry.DLQ = true`  

`idempotency = required (key strategy named)`  

`worker.concurrency = 5`  

plus **ownership** (which component enforces retries vs business idempotency) and pointers to acceptance ids.

Implement only after SPEC doc (or excerpt) exists; after code, compare **SPEC ↔ code/tooling** systematically.

---

### Specification runtime worksheet (minimal)

| Block | Holds |
|-------|-------|
| **SPEC VERSION** | Id + frozen excerpt / link. |
| **ACCEPTANCE** | Checkbox bullets tied to tests or scripted checks where possible. |
| **OWNERSHIP** | Who answers for each invariant (domain vs infra). |
| **CONSTRAINTS** | Hard rules (libraries, layering, patterns). |
| **NFR** | Latency, availability, throughput, audit—what “good” means numerically where applicable. |
| **VERIFICATION PLAN** | How each line above is proved post-implementation. |
| **DRIFT LOG** | Mismatches found + repair actions—dated. |

Themes mapped: **executable spec**, **implementation ownership** (carry worksheet forward), **acceptance ownership** (who signs verification).

---

**Practice slices**

Symfony **CQRS payment** slice—freeze command/handlers, aggregates, projector expectations before codegen momentum.  

Go **worker queue** + **RabbitMQ** semantics—explicit ack, prefetch, DLQ routing in spec verbs.

### LAB invariant

Every task:

**Before:** author compact **executable spec artefact.**  

**After:** run **SPEC ↔ implementation** reconciliation table—anything undefined is flagged as deliberate debt or SPEC bug.

### Checklist

- [ ] Acceptance lines are falsifiable—“works” without observable signal is forbidden.  
