# Ansible — `09-terraform-ansible-full-stack-integration`

**Focus:** End-to-end lab — Terraform provisions AWS infrastructure, Ansible configures application layer, GitLab CI orchestrates the full pipeline.

**Practise focus**

- Terraform creates: VPC, public subnet, security group, EC2 instance (with keypair), outputs instance public IP
- Terraform `local-exec` provisioner writes IP to `ansible/inventory/hosts` after apply (or use Terraform output + CI step)
- Ansible playbook runs post-Terraform: installs Docker, copies application config via template (with vault-managed DB password), starts application container
- GitLab CI pipeline: `terraform plan` → approval gate → `terraform apply` → `ansible-playbook site.yml` → smoke test (curl health endpoint)
- Handle failures: Terraform apply fails → Ansible never runs; Ansible fails → instance exists but is unconfigured → fix and re-run Ansible only
- Teardown: `terraform destroy` cleans infrastructure; no Ansible cleanup needed (infra gone = config gone)
- Reflect on the boundary: Terraform owns infrastructure lifecycle, Ansible owns software configuration lifecycle — neither crosses into the other's domain
