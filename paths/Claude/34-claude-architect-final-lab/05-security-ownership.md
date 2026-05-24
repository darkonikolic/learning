# Security ownership

**Unit:** `05` (week 5)—production security intersecting AI-assisted workflows.

### Topics

**Prompt injection** resistance in operational prompts and Rules  

**Secret exposure** — no prod keys through model context; redaction discipline  

**Permission ownership** — tool/MCP scopes match least privilege  

**Unsafe approval** — no skips on destroy-class or credential paths  

Credential handling patterns (Symfony **JWT**/OAuth flows, Go service identity to dependencies)

### Threat modeling ownership (engineering, not slideware)

**STRIDE catalogue** exercised against at least:

Public payment API façade  

Webhook/PSP ingress  

Queues + worker privilege boundary  

Operational/admin surfaces  

Assistants/rules execution environment (credential exfil pathways)

For each relevant STRIDE pillar (**Spoofing, Tampering, Repudiation, Information disclosure, Denial of service, Elevation of privilege**) record:

Asset affected • realistic abuse • detection signal • mitigation owner • residual risk tier  

**Attack surface modeling** shrink plan: MCP scopes, SSRF-able callbacks, webhook replay, JWT validation gaps  

Templates + examples: **`09-enterprise-depth-appendix.md` § Threat modeling & STRIDE.**

### Adversarial LAB

Introduce an **unsafe workflow** path (fabricated)—assistant stack must **detect**, **block**, and **repair** posture (policy + human gate), not comply.

### Checklist

- [ ] Approval matrix referenced for any change that touches identity, secrets, or prod destroy verbs.  

- [ ] STRIDE worksheet stored next to SPEC revision—security moves with architecture deltas.  
