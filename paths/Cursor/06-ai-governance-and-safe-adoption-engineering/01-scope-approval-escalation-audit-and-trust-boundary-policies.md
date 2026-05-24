# Unit 1 — Scope: AI governance engineering — policy becomes product

Mindset shift: assistant usage is an **operational surface** — approvals, audit, escalation, least privilege.

## Learning outcomes

- **Approval workflows**: when human sign-off mandatory (schema, auth, billing, PII).
- **Human approval gates** vs automated checks—matrix by risk class.
- **Escalation ownership**: ambiguous security → security owner, not smartest IC guess.
- **Fallback ownership**: degrade to manual authoring / smaller model / narrower tool window.
- **Audit ownership**: what gets logged (prompt ids, approvals, artefacts) respecting privacy/reg constraints.
- **Operational policy**: permissible data classes in AI context windows.
- **Compliance hooks**: DPIA-lite thinking, residency awareness (high-level, verify legally).
- **Rollback / incident hooks**: revoke tokens, purge cached context exposures.
- **Governance RACI overlay** for organisational AI adoption.
- **Trust boundary ownership**: where AI suggestions **must not cross** CI secrets, prod creds paths.
- **Safe generation posture**: forbid secret pasting patterns, red-team self prompts.
- **Permission ownership**: aligning repo privileges with assistant capabilities / MCP tooling.
- **Organisational AI rules layering**: Cursor rules vs central policy vs team conventions—conflict precedence.

Feeds production alignment **`20-*`**, tooling **`14-*`**, verification **`07-*`**.
