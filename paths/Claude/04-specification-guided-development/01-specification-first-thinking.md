# Specification-first thinking

## Phase framing (Specification Guided Development)

**Highest-leverage framing for this track:** validated **specification before** substantial implementation churn.

Topics **`01`–`08`**.

### Core workflow

```
Problem → Specification → Architecture → Implementation → Validation
```

**Validation ownership:** you compare each delivered increment against SPEC + acceptance + NFR **before** the next slice merges. Claude assists — **you** keep veto/sign-off.

### Mindset shift

| Stop | Start |
|------|-------|
| “Build it”, then regret in code | **Problem → SPEC → bounded plan → code** |

### Exit criteria for this curriculum

Before non-trivial **Symfony**, **Go**, **Terraform**, or **MySQL** churn in these exercises you can produce a SPEC artefact: problem, acceptance, boundaries where needed, constraints/NFR, implementation strategy — **before** IDE-driven delivery.

### Practice stacks here

Symfony (PHP / DDD / CQRS) • Go APIs/workers • Terraform • MySQL truth for data+NFR workloads.

### Theme checklist across units

Specification first • acceptance criteria • boundaries/ownership • constraints + NFR • implementation specification • validation ownership • spec evolution • drift detection • partition • dependency graph • cross-spec consistency • ownership hierarchy among SPECs.

### Checkpoint wording

Prefer **Claude implementing a SPEC** — not prompting straight to unsolicited large codebases.

---

## Unified SPEC template (same spine for Symfony, Go, Ops/IaC, MySQL-backed work)

Use the same headings; omit only what truly does **not** apply. Never skip **Acceptance** nor **validation** when behaviour moves.

| Section | Purpose |
|---------|---------|
| **Problem** | Grounded sentence + why now. |
| **Goal** | Measurable organisational outcome where possible. |
| **Constraint** | Hard bans / compulsory stack rules. |
| **NFR** | Throughput, availability, latency, audit, retention, safety baselines — mark hypothesis vs measured. |
| **Boundary / ownership** | Which context/module owns decisions (`Order`, `Payment`, `Inventory`, …). |
| **Acceptance** | Short checkable behaviours (often **≥5** on feature-sized slices). |
| **Implementation Strategy** | Modules, rollout, infra touchpoints — **spec fidelity**, still not pasted production code dumps. |
| **Tradeoff** | ≥2 plausible options + deliberate pick. |
| **Risk** | First-failure modes, mitigations, unknowns. |
| **Implementation spec** (when warranted) | Named tech + numeric knobs (e.g. RabbitMQ retries=**3**, DLQ policy, timeouts, worker counts) immediately **before coding**. |

**Cross-spec consistency:** if several SPECs exist (`api`, `worker`, `db`, `terraform`) keep a terse **dependency/consistency ledger** referencing shared noun definitions so they cannot silently diverge (“must agree column X semantics”).

**Ownership hierarchy:** parent programme SPEC adjudicates clashes; child bounded-context SPEC cannot quietly violate parent acceptance.

---

**Theme:** The largest tactical shift — Claude gets SPEC-shaped answers **before** wall-of-code drive-by.

### Bad vs good

**Weak:** “Build an order system.”  

**Stronger starting skeleton:**

- **Problem:** truthful **order flow** span.  
- **Goal:** purchase outcomes you certify.  
- **Constraint:** **refund**, **cancel**, **retry**, **audit** inside scope fences.  
- **NFR (starter):** e.g. cite **500 rps target** honestly as throughput hypothesis pending measurement.

Produce **readable SPEC** collaborators accept before implementation begins.

### Practice

| Track | Micro-focus |
|-------|--------------|
| **Symfony** | **Order aggregate** invariants enumerated before method sketches. |
| **Go** | **Worker / queue contracts** articulated before handlers. |

### Lab — invariant rule

Every sizeable task ships a SPEC Markdown using the **unified headings above** *before* diff-sized implementation output.

Reflect: enumerate ≥3 branching unknowns extinguished SPEC-first vs impulse coding.

### Checklist

- [ ] Separate visible blocks exist for **Problem / Goal / Constraint / starter NFR**.  
- [ ] Model’s heavyweight first replies stay SPEC-shaped whenever change risk is meaningful.  
