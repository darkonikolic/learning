# Ansible — `04-roles-structure-and-reuse`

**Focus:** Organise playbook logic into roles — reusable, testable units with a conventional directory structure. Roles are how real teams share and version Ansible code.

**Practise focus**

- Generate a role scaffold with `ansible-galaxy init myrole`; understand `tasks/`, `handlers/`, `templates/`, `files/`, `vars/`, `defaults/`, `meta/`
- Difference between `vars/` (high priority, not easily overridden) and `defaults/` (low priority, meant to be overridden)
- Write a `nginx` role: install, configure with a Jinja2 template, enable and start
- Apply the role in a playbook via `roles:` key; override defaults with `role_params`
- Install a community role from Ansible Galaxy: `ansible-galaxy install geerlingguy.docker`
- Pin role versions in `requirements.yml`; install with `ansible-galaxy install -r requirements.yml`
- Understand role dependencies via `meta/main.yml`
- Structure a real project: `site.yml` → `roles/` → `group_vars/` → `inventory/`
