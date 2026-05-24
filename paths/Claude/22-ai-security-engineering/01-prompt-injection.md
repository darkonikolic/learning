# Prompt injection — AI security framing

## Phase framing — AI Security Engineering (“Phase 8.8”)

**Units in this folder:** `01`–`06` (topic order only).

### Mindset pivot

Assume **every AI step is an exposed surface**. Security is not the absence of attackers—it is layered **trust boundaries**, **distrusted inputs**, **tool scepticism**, and **controlled approval**—especially wherever **Ops**, **IaC**, **MCP**, and **agents** widen capability.

Comfort target: a composed Claude-style system **detects coercion**, refuses **secret exfiltration**, blocks **unsafe approval skips**, and recovers **without collapsing** unrelated work—not “we trust the assistant.”

### Theme map for this syllabus

**Prompt injection**  

**Tool / MCP injection**  

**Permission boundaries**, **least privilege**, **approval workflow**  

**Secret exposure** risk & redaction discipline  

**Memory / context poisoning** (shared knowledge lies)  

**Agent security** (role abuse, escalation mistakes)

These topics are **obligatory** when you tie AI to operations and infrastructure—you are not practising optional hardening fluff.

### Claude Security Template — for serious workflows

| Field | Holds |
|-------|-------|
| **INPUT TRUST** | Classes of inputs (trusted operator, untrusted docs, scraped pages, pasted logs)—default **distant** until classified. |
| **TOOL TRUST** | MCP / shell / browser / file tools: assumed **hostile-ish** outputs; verification before acting on them. |
| **MEMORY TRUST** | Retrieval & long-lived summaries: authoritative sources, versioning—poison detection strategy. |
| **SECRET RISK** | Credential classes that must never traverse model context; detectors & redactors. |
| **PERMISSION MODEL** | Capability matrix (read diagnostics vs mutate infra vs destructive). |
| **APPROVAL MODEL** | Mandatory human / role gates aligned to blast radius—not theatre. |
| **ESCALATION** | Paths when suspicion rises (isolate session, widen review, revoke tokens). |
| **BLOCK POLICY** | Explicit deny rules (credential echo, unrestricted destroy, wildcard deletes). |

**Checkpoint mantra:** the goal is not merely “AI works”—**AI works safely** under adversarial and sloppy-input reality.

Sandbox / containment patterns you learnt elsewhere complement this—reuse them in design, do not reinvent casually.

---

**Theme (this unit): Prompt injection**

Attacker goal: reorder **instruction hierarchy** so untrusted blobs masquerade as system truth—classic patterns include “Ignore all rules”, “Print prior system prompt”, “For debug dump secrets / env vars.”

Defensive habits:

Maintain clear **trusted vs untrusted** instruction strata—nothing from scraped web content or hostile tickets merges silently with operator intent. Treat embedded documents as attacker-controlled until audited. Prefer **immutable policy** artefacts (RULES, pipelines) enforcing refusals the model alone cannot casually erase.

Operational posture: refusal + **narrow continuation** beats verbose debate with attackers.

LAB: compose **minimum ten benign-style injection exemplars** in a disposable environment—observe whether refusal classifies cleanly and workflow continues minus harmful compliance.

### Checklist

- [ ] No security-sensitive workflow relies solely on brittle phrasing—“please don’t”—without structural gates (scopes, approvals, secret managers).  
