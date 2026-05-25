# Ansible — `01-ansible-mental-model-and-why-it-exists`

**Focus:** Understand where Ansible sits in the toolchain — Terraform creates infrastructure, Ansible configures what runs on it. Agentless push model via SSH.

**Practise focus**

- Distinguish configuration management (Ansible) from infrastructure provisioning (Terraform) — the handoff boundary
- Understand the push model: control node SSHes into managed nodes, no agent required
- Install Ansible on a control node; confirm `ansible --version` and Python dependency chain
- Run first ad-hoc command: `ansible all -i hosts -m ping`
- Understand idempotency as the core contract — running a playbook twice must produce the same state
- Compare Ansible vs Chef/Puppet/Salt — why Ansible won on simplicity and agentless architecture
- Identify real-world use cases: EC2 post-provision setup, config drift remediation, patch management
