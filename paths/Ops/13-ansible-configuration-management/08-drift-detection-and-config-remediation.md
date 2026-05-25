# Ansible — `08-drift-detection-and-config-remediation`

**Focus:** Detect and correct configuration drift on live servers — the operational superpower that justifies Ansible alongside Terraform and Kubernetes.

**Practise focus**

- Run a playbook in `--check` mode on a production host to surface drift without making changes
- Schedule nightly drift detection in CI: playbook runs in check mode, fails pipeline if drift detected, pages on-call
- Simulate drift: manually change nginx config on a server; re-run playbook and confirm it corrects back to desired state
- Use `assert` module to validate invariants (file exists, service is running, port is open) as a health-check playbook
- Understand the limits of idempotency: `command`/`shell` modules are not idempotent by default — use `creates` / `removes` guards or prefer purpose-built modules
- Distinguish Ansible remediation (immediate SSH-push fix) vs Terraform remediation (state reconciliation) — choose based on what drifted
- Build a simple audit playbook: check OS patch level, verify no unauthorized users, confirm firewall rules — output a report
