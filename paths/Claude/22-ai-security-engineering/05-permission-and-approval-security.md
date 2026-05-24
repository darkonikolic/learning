# Permission + approval security

**Theme:** Highest blast-radius failures pair **powerful tooling** with **thin guardrails.**

Anti-patterns enumerated bluntly:

Unreviewed **`terraform apply`**, unrestricted **`kubectl delete`**, sweeping credential exports, autop-run migrations against shared prod without CAB discipline.

Prefer structured choreography:

Assistants produce **plans / diffs / dry-runs**

Humans classify risk lane

Execution occurs under scoped credentials & logging

Mandatory artefacts:

| Class | Typical posture |
|-------|-------------------|
| **SAFE** read diagnostics, logs (non-secret), narrowly scoped filesystem listing |
| **APPROVAL** schema migrations impacting shared services, infra changes with partial blast |
| **CRITICAL / dual** destroy-class operations & secret touching |
| **FORBIDDEN** unbounded deletes, dumping secret files, circumventing MFA assumptions |

Mandatory lab expansion: annotate **trust level per tool/integration** analogous to MCP server capability tiering—destructive combos demand narrow identity & short TTL tokens.

Discuss **permission model drift**: periodic audits since automation silently widens IAM—AI accelerates exploitation if drift unnoticed.

Discuss **approval theatre**: meaningless rubber stamps—increase specificity of reviewer checklist realism.

Concurrency between agents: approvals **non-transferable implicitly** unless explicit delegation recorded.

### Checklist

- [ ] Applies & deletes log **immutable correlation ids** aiding future incident timelines—not ephemeral chat-only trace.  
