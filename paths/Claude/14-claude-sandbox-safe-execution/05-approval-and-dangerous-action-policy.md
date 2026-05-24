# Approval + dangerous action policy

**Theme:** Production discipline for AI-mediated ops: **propose → plan → human approval → execute** — never autopilot destructive CLIs.

### Pattern contrast

Weak: assistant → **`terraform apply` / `kubectl delete` / production migration** unattended.  

Strong: assistant → **`terraform plan` / dry-run manifest / migration SQL review** → **human sign-off** → executed in controlled CI or bastion—with logs.

### Forbidden-class examples

`rm -rf` on ambiguous paths  

`terraform destroy`, mass `kubectl delete` without scope guardrails  

Exporting prod credentials into shell env visible to tooling

### Classification LAB

For recurring commands (`git push`, migrations, infra applies, Helm upgrades), tag each:

- **SAFE** — read-only diagnostics, formatted logs  

- **NEEDS_APPROVAL** — mutates shared state  

- **FORBIDDEN** — violates secret or prod-touch policy  

Automation (hooks, MCP tools, IDE tasks) maps to the **same** classes—parity matters.

### Checklist

- [ ] Approval model written down where **you** rehearse—not only where the vendor UI happens to pause.  
