# STRIDE — threat modeling framing

## Phase framing — Threat Modeling Engineering (“Phase 8.85”)

**Units in this folder:** `01`–`04` (topic order only).

### Mindset pivot

Move from reactive **security review checklists** toward explicit **ownership** of threats and risks tied to assets you actually run (Symfony APIs, Go workers, JWT/OAuth fronts, queues, Terraform, MCP-enabled workflows).

Operational spine reused every time you widen the system surface:

```
 ASSET enumerated
       → THREAT articulated (often STRIDE-labelled)
               → RISK scored / prioritised honestly
                           → MITIGATION chosen (design + ops)
                                              → VERIFICATION proving controls help (tests, scanners, drills)
```

### Theme map across this syllabus

**STRIDE** taxonomy discipline  

**Attack surface modeling** (“what can be touched by whom”)  

**Trust boundaries** (what you trust—and must not trust by default)

Cross-cutting ownership: **threat ownership** (who watches which abuse story), **risk ownership** (who accepts residual), **privilege escalation** patterns as a recurring STRIDE pillar

### Lightweight threat slice worksheet — paste per feature or epic

| Step | Holds |
|------|-------|
| **ASSET** | Data, code path, infra object, credential, identity—be specific. |
| **THREAT** | Abuser story using STRIDE label where it fits (see below). |
| **RISK** | Likelihood + impact rationale (simple matrix is fine at first). |
| **MITIGATION** | Architectural, procedural, cryptographic—paired to threat. |
| **VERIFICATION** | How you know mitigation stayed true (automated checks, audits, red team note). |

**Checkpoint mantra:** you stop treating security as a one-off review pass and start carrying **security ownership** alongside feature ownership.

This complements **AI Security Engineering** (prompt/tool abuse): here the primary lens is classical system threat modeling—with AI-augmented delivery as one more surface inside attack surface maps.

---

**Theme (this unit): STRIDE**

| Letter | Means | Prompt |
|--------|-------|--------|
| **S** Spoofing | Pretending to be someone/something else | Who authenticates identities? Replay? Token theft? |
| **T** Tampering | Altering data or code at rest/transit/runtime | Integrity controls on queue payloads, manifests, binaries? |
| **R** Repudiation | Denying an action occurred | Logs, immutable audit IDs, transactional evidence? |
| **I** Information disclosure | Exposing secrets/data to wrong principals | Overscoped JWT claims, leaky errors, verbose logs? |
| **D** Denial of service | Taking availability away | Queue saturation, DB pool drain, expensive endpoints? |
| **E** Elevation of privilege | Doing more than allowed | JWT scope widen, IaC impersonation drift, MCP over-permission |

LAB: Pick one subsystem slice (Symfony controller pair, Go handler, infra module) and list **minimum two plausible threats per STRIDE category you honestly care about for that slice—not boilerplate fantasies.**

### Checklist

- [ ] STRIDE passes include **trust boundary crossings** explicitly—attacks love edges.  
