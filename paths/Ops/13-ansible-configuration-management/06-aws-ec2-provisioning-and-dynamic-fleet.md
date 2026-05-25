# Ansible — `06-aws-ec2-provisioning-and-dynamic-fleet`

**Focus:** Use Ansible to configure EC2 instances after Terraform creates them — the standard post-provisioning handoff pattern for AWS fleets.

**Practise focus**

- Use `amazon.aws.ec2_instance` module to launch an EC2 instance from Ansible (understand when this vs Terraform is appropriate)
- More common pattern: Terraform outputs instance IPs → write to dynamic inventory → Ansible picks up and configures
- Implement the handoff: Terraform `output "instance_ips"` → local-exec writes `inventory/hosts` → `ansible-playbook site.yml -i inventory/`
- Configure a freshly launched EC2: install Docker, configure logging, set up a systemd service
- Use EC2 tags as inventory groups via dynamic inventory plugin — no static IP management
- Handle SSH key injection: Terraform places keypair, Ansible uses `ansible_ssh_private_key_file`
- Run Ansible from GitLab CI after `terraform apply` succeeds — full automated provision + configure pipeline
