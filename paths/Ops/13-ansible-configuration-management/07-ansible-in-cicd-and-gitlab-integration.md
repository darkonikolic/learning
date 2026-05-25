# Ansible — `07-ansible-in-cicd-and-gitlab-integration`

**Focus:** Run Ansible playbooks from GitLab CI — authenticated, vault-aware, and scoped to the right environment via protected variables.

**Practise focus**

- Add an `ansible` stage to `.gitlab-ci.yml` after the `deploy` (Terraform) stage
- Install Ansible in a CI job using a Docker image (`cytopia/ansible` or build your own)
- Inject vault password via GitLab CI protected variable (`ANSIBLE_VAULT_PASSWORD`); write to temp file, clean up after run
- Use `ansible-lint` as a quality gate job — fail pipeline on playbook violations
- Scope playbook execution to environment: `staging` branch runs against staging inventory, `main` against production
- Use GitLab environments to track which Ansible version last ran against each host group
- Cache `ansible-galaxy install` output as a CI artifact to avoid re-downloading roles on every run
- Debug failed CI runs: `ansible-playbook -vvv` output in job logs, interpreting SSH errors vs task failures
