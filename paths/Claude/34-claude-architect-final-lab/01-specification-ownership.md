# Specification ownership — final lab framing

## Phase framing — Claude Architect Final Lab (“Faza 12”)

**Capstone:** End-to-end **Payment Platform** you drive with assistant orchestration—not isolated coding exercises.

**Core units:** `01`–`08` (topic order). Companion file **`09-enterprise-depth-appendix.md`** is the **explicit depth syllabus** critics expected (tests, distributed systems, observability, Go perf, K8s prod, DB enterprise, STRIDE)—use it alongside **the numbered units (`01`–`08`)** as needed; it does not replace ownership artefacts in `01`–`08`. Broj faz u **`paths/Claude/NN-*`** može da raste kad proširiš plan (npr. `35`–`43`).

### Engineering spine (north star—adapt evidence to your sandbox)

```
 SPEC  →  Architecture  →  PHP (Symfony CQRS lanes)  →  Go (workers)
        →  DB / MySQL + messaging (e.g. RabbitMQ)   →  Ops (Docker/K8s)  →  IaC (Terraform)
              →  Security  →  Deploy  →  Incident  →  Optimization
```

**Goal shift:** Claude no longer solves **fragments** disconnected from ownership—you run a **system** whose lifecycle you steer and measure.

**Success criterion artefact clusters:** coherent **ownership model**, surfaced **tradeoffs**, explicit **risk** registers, reproducible **rollback** stories, **failure ownership**, honest **scaling** posture—documented—not chat-only folklore.

---

## Week 1 — Specification ownership

**Theme:** Everything **starts** from a governed specification—not wishful backlog blur.

### Platform slice — initial REQUIRED headings (grow deliberately)

Functional areas (examples—tighten to your domain language):

Payment API surfaces  

Refund choreography  

Inventory coupling / reservation semantics  

Outbound **notification** contracts  

Tamper-evident **audit** trail commitments  

Operational **retry** / **DLQ** policies  

Mandatory **idempotency** modelling

Representative executable **NFR** seeds (adjust to realism):

Throughput class **≈1000 sustained req/s** hypothetical load model anchor  

Availability narrative **≈99.95%** with explicit carve-outs dependent on PSP infra honesty  

Formal **audit ownership** assignments (who asserts immutable evidence integrity)  

**Rollback ownership**: who invokes retreat & ordering constraints bridging DB/schema vs runtime

### Practice linkage

Symfony: **CQRS payment aggregate** invariants enumerated before codegen.  

Go: worker **ownership** boundaries (consume, ack, poison, reconcile) penned plainly.

### LAB deliverables

Produce living bundle:

`spec` synopsis **→** enumerated **acceptance** criteria keyed for tests  

`constraint` bullets (architecture / tech stack / compliance immutables)

`NFR` table with verifier hook ideas—even if stubs initially  

### Test-engineering linkage (still Week 1: plan the rails)

Each acceptance/NFR cluster should declare **what test class proves it**, not vibes:

| Class | Pays for (payment platform exemplar) |
| ----- | -------------------------------------- |
| **Unit** | Domain invariants (idempotency keys, ledger rules), pure policy |
| **Integration** | API + DB boundary, saga step + repository, queue adapter (test container / docker) |
| **Contract** | Published API/message schemas versus consumers/providers (payments vs notifications PSP façade) |
| **Property-based** | Invariants generators should never break (`Refund ≤ captured`, replay safety) |
| **Load** | Sustained throughput, tail latency ceilings under contention (tie to ~1000 rps story if you adopted it) |
| **Chaos** | Controlled fault injection hypotheses (broker blip, slow DB)—expected steady-state behaviours named in SPEC |

Detailed patterns and tooling posture live in **`09-enterprise-depth-appendix.md` § Test engineering.**

### Obligations this week reinforces

 Specification discipline  

 Boundary **ownership** language  

 Acceptance criteria crystallised so Weeks 3+ can tie **verification** without reinterpretation drift

### Checklist

- [ ] No acceptance line remains purely subjective mood adjectives—tie each to observable signal roadmap.  
