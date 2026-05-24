# Goal decomposition

## Phase framing — Goal / Process Driven Development

**Area topics:** `01`–`06` (topic order only).

### Delivery spine (engineering process shape)

```
Goal  →  Spec  →  Task graph  →  Implementation  →  Validation
```

**Mindset pivot**

| Old reflex | Owned reflex |
|------------|---------------|
| “Feature idea” → rush to code chunks | **Goal → process clarity → executable task graph → delivery evidence** |

**Exit bar**

When asked *“build a payment platform”*, **first artefacts** tilt toward:

- articulated **goal** + **ownership**  
- workflow / **task decomposition**  
- **risk** surface  
- **validation** posture  

…rather than dumping code volume before reasoning is inspectable.

**Themes threaded across units:** goal decomposition • workflow ownership • validation loop • verification loop • rollback ownership • optimization ownership  

---

## Claude Goal Template (use consistently)

Same headings for Symfony, Go, Ops/IaC, and DB-heavy work:

| Heading | Holds |
|---------|-------|
| **GOAL** | Outcome sentence + measurable north-star boundary. |
| **SUCCESS CRITERIA** | Checkables (acceptance-aligned). |
| **WORKFLOW** | Ordered stages artefacts traverse (diagram + captions). |
| **OWNERSHIP** | Roles / bounded contexts owning each slice. |
| **RISK** | What fails first — technical + human process. |
| **VALIDATION** | Proof that behaviour meets intent (“does it run / do the checks pass”). |
| **ROLLBACK** | Safe unwinding when validation discovers fatal mismatch. |
| **OPTIMIZATION** | Complexity / cost / latency improvements after baseline safety holds. |

You may prepend **SPEC bullets** beside Goal when practising with Specification Guided habits from earlier phases.

---

**Theme:** Decompose ambiguous platform asks into navigable hierarchies instead of hallucinated single-file leaps.

### Bad vs grounded

**Weak:** “Make a payments system.”  

**Strong:**

- **GOAL:** a named **payment platform slice** with integrity guarantees you state outright.  

Show **≥ three decomposition depths**, for example:

```
payment API strand
  ├─ retry ownership
  │    └─ idempotency rules
inventory alignment strand
notifications strand
audit / trace strand
refund choreography strand
```
Drill deeper on one strand:

```
payment API
  └─ auth perimeter
       └─ request validation gates
           └─ timeouts coexisting with retries
```

### Practice rotations

| Track | Skeleton focus |
|-------|----------------|
| **Symfony** | **CQRS refund flow** slicing commands vs queries. |
| **Go** | **Worker system**: lifecycle, backoff, poison handling decomposition. |
| **Ops** | **Terraform deploy** stages with checkpoints inside task graph prose. |

### Lab rule

Each exercise-sized backlog item: **minimum three decomposition layers** before scaling implementation discussion.

### Checklist

- [ ] Level-one bullets describe **capabilities**, not incidental file churn.  
- [ ] Leaves cite **verification** you intend to automate or script soon.  
