# Unit 1 — Scope: tool orchestration — reliability of capability surfaces

Mindset shift: MCP / terminal / browser tooling extends reach — expands **failure + permission** frontier.

## Learning outcomes

- **Tool routing rationale**: cheapest reliable truth path first (git status vs speculative reasoning).
- **Capability ownership**: which tools permissible per risk envelope (`06-*` alignment).
- **Retry etiquette**: differentiated for idempotent reads vs destructive writes.
- **Fallback ladders**: degraded manual path when tooling flakes.
- **Tool degradation signalling**: timeouts, truncated JSON, stale workspace roots.
- **Partial failure narratives**: half-applied filesystem patch + transactional thinking.
- **Approval boundaries intersecting tooling**: prompts that could exfil secrets must be gated.
- **Permission ownership hooks**: scopes / PAT lifetimes principle-level.
- **Retry escalation thresholds** → human when consecutive autonomous failures accumulate.
- **Recovery ownership**: rewind local partial apply / reclone cautions high-level.
- **Verification tying**: rerun failing command proving fix post tool-assisted patch.
