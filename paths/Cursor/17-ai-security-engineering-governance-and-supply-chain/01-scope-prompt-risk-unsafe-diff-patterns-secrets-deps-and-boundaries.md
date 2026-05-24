# Unit 1 — Scope: AI security engineering — threat model for accelerated change

Mindset shift: copilots expand **attack surface velocity** — prompt + tool + dependency fronts.

## Learning outcomes

- **Prompt injection awareness**: untrusted content vs trusted instructions; poisoning via pasted logs or issue bodies.
- **Unsafe generation detection heuristics**: secret patterns, credential sprawl, destructive mass operations, privilege escalation templates.
- **Trust boundaries**: where AI suggestions halt pending human escalation.
- **Approval boundaries** tying sensitive infra / billing / PII-touching merges.
- **Dependency trust uplift**: pinning, integrity verification, deprecation of speculative “nice” libraries sourced only from completions.
- **Secret ownership rituals**: forbidding pasted tokens into assistant windows; ephemeral env segregation.
- **Dependency security scanning synergy** connecting review flow + codegen suggestions.
- **Permission ownership**: least-privilege MCP / CI PAT scopes; rotation intuition.
- **Supply chain scepticism**: copy-pastes of unknown snippets flagged before merge.
- **Validation discipline** reinforcing “assume hostile diff until proven benign”.
- **Attack surface enumeration** augmented with automation hooks (`git`, browser, MCP file writes).
- **Safe execution / sandbox instincts** aligning with organisational policy (`06-*`).
- **Context isolation**: dataset separation preventing accidental leakage of staging prod-like fixtures into logs committed for assistance.
