# Sandbox thinking — safe execution framing

## Phase framing — Claude Sandbox / Safe Execution Environment (“Phase 6.5”)

**Units in this folder:** `01`–`06` (topic order only).

### Goal trajectory

Shift from **assistants exercising power directly on the host** toward **controlled execution surfaces**: bounded filesystem, narrowed network, rotated non-production secrets, explicit human approval gates, rehearsed rollback.

Comfort target: calmly using helpers with **Symfony**, **Go**, **Terraform**, **Docker**, **Kubernetes**, **MySQL**, **debug / incident** workflows, **MCP servers**, and **agents**—without treating any of them as implicitly safe.

### Host vs isolation shapes (vocabulary)

| Surface | Role |
|---------|------|
| **Host** | Your machine or shared CI runner—highest trust, largest blast radius. |
| **Sandbox** | Deliberate boundary (VM, container, dedicated user, remote env) where damage is contained. |
| **VM** | Strong isolation; heavier to run. |
| **Container** | Lighter process + filesystem + network boundary—not a security panacea alone. |
| **Devcontainer** | Standardised dev workspace image + mount policy—convenience **plus** policy if you enforce it. |

### Boundaries to name in every design

**Isolation boundary** — what the tool literally cannot reach.  

**Trust boundary** — what you assume about code, models, and third-party tools.  

**Permission boundary** — read / write / execute explicitly scoped.  

**Blast radius** — worst plausible outcome if the boundary fails.

### Operating contrast

**Weak pattern:** assistant → shell → full host authority.  

**Strong pattern:** assistant → **declared workspace** → **scoped credentials** → **approved** high-risk steps → **recoverable** state.

### Claude Sandbox Template — use for every serious project

| Field | Holds |
|-------|-------|
| **WORKSPACE** | Single root path(s) where AI/tooling may read/write; what is out of bounds. |
| **FILESYSTEM ACCESS** | Read-only vs read-write mounts; ban list (`/`, `$HOME` wholesale, sibling repos). |
| **NETWORK ACCESS** | Allow/deny posture (docs only, package registries, internal API mock, full internet—justify). |
| **SECRET ACCESS** | Which fake or scoped credentials exist; what must **never** be mounted or exported. |
| **TOOL ACCESS** | Shell, git, DB client, `kubectl`, cloud CLIs—each with scope notes. |
| **PERMISSION MODEL** | Map actions to least privilege; default deny for destructive ops. |
| **APPROVAL MODEL** | What runs only after human review (`terraform apply`, prod `kubectl`, migrations). |
| **ROLLBACK MODEL** | Revert images, Terraform state discipline, DB migration reversals—what is possible. |
| **BLAST RADIUS** | Short paragraph: worst case if this config is wrong. |

### LAB (this unit)

For each recurring **Claude / agent / MCP** workflow you use, write two columns: **allowed** and **forbidden**—then fold them into the template above.

### Checklist

- [ ] You can explain **where** execution runs (host vs container vs remote) without hand-waving “the AI just helps.”  
