# Domain modeling and requirements

## Phase framing — Claude Architect Workflow (Phase 5)

**Units in this folder:** `01`–`06` (topic order only).

### Themes across this area

**DDD** • **CQRS** • **scaling** • **cache strategy** • **event-driven** design • **ownership** • **tradeoff analysis** • **boundary ownership** • **failure ownership**

### Architect workflow spine (each significant slice)

```
Requirement  →  Architecture  →  Tradeoff  →  Risk  →  Implementation plan  →  Validation
```

Aligned with **Symfony**, **Go**, **MySQL**, and **distributed-systems** realities (partitions, duplication, partial failure).

### Reaction you want when someone says “build a payment platform”

First artefacts skew toward **goal / ownership / workflow / task decomposition / risk / validation** — **not** a wall of unpremeditated code.

### Claude Goal Template (same headings everywhere: Symfony / Go / Ops / DB)

| Heading | Holds |
|---------|-------|
| **GOAL** | Outcome and scope boundary. |
| **SUCCESS CRITERIA** | Checkable acceptance bullets. |
| **WORKFLOW** | How responsibility and data move (diagram + captions). |
| **OWNERSHIP** | Contexts, teams, components that **decide** and **run** each slice. |
| **RISK** | Failure and scaling assumptions surfaced early. |
| **VALIDATION** | How you prove “works as intended”. |
| **ROLLBACK** | Safe retreat when validation fails badly. |
| **OPTIMIZATION** | Complexity / cost / latency improvements **after** baseline safety. |

### Claude Architect spine (use alongside or inside the template)

Map **Requirement** into Goal + SUCCESS CRITERIA; **Architecture** + **Tradeoff** + **Risk** as explicit sections; **Implementation plan** as sequenced tasks with owners; **Validation** tying back to SUCCESS CRITERIA.

---

**Theme (this unit):** **Specification-first domain shape** — DDD aggregates and boundaries, CQRS separation of intents, decomposition before hype coding.

### Bad vs grounded

**Weak:** “Build a payments system.”  

**Strong:** Named **payment platform slice** plus **three+ levels** of decomposition, for example:

```
payments API strand
  ├─ auth / identity touchpoints
  ├─ idempotency + retry posture
inventory / fulfilment coupling
notifications
audit & refund choreography
```

### Practice rotations

| Stack | Drill |
|-------|-------|
| **Symfony** | **CQRS refund flow** — command vs query ownership, aggregates. |
| **Go** | **Worker subsystem** decomposition (lifecycle, poison, backoff). |
| **Ops / IaC** | Terraform (or equivalent) staged rollout encoded as workflow steps **with** explicit rollback hooks. |

### Lab rule

Every exercise task: document **minimum three decomposition levels** **before** an implementation-plan paragraph grows fat.

### Checklist

- [ ] Nouns (**Order**, **Payment**, **Ledger**) have **bounded** meanings per context.  
- [ ] CQRS split answers **who reads what model** vs **who changes state**.
