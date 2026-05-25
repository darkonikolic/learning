# Ansible — `02-inventory-static-and-dynamic`

**Focus:** Define and manage inventories — static INI/YAML files for fixed infrastructure, dynamic inventory plugins for AWS EC2 where IPs change on every deploy.

**Practise focus**

- Write a static `inventory.ini` with groups (`[webservers]`, `[databases]`) and host variables
- Convert to YAML inventory format; understand `host_vars/` and `group_vars/` directory conventions
- Install and configure the `amazon.aws.ec2` dynamic inventory plugin; authenticate via IAM role or credentials
- Run `ansible-inventory --list` to inspect resolved host list from AWS
- Filter dynamic inventory by EC2 tags (`Environment=staging`, `Role=api`) — target only relevant instances
- Understand `all` and `ungrouped` built-in groups; compose nested group hierarchies
- Test inventory with `ansible all -m ping` against a real or LocalStack-backed EC2 mock
