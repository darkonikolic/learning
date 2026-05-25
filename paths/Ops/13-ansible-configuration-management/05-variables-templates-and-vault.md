# Ansible — `05-variables-templates-and-vault`

**Focus:** Manage configuration data cleanly — Jinja2 templates for dynamic files, variable precedence hierarchy, and Ansible Vault for secrets.

**Practise focus**

- Write a Jinja2 template (`nginx.conf.j2`) with variable interpolation and conditional blocks; deploy with `template` module
- Understand variable precedence order (22 levels) — know that `extra_vars` (`-e`) always wins, `defaults/` always loses
- Define environment-specific vars in `group_vars/staging/` vs `group_vars/production/`
- Encrypt a secrets file with `ansible-vault encrypt secrets.yml`; decrypt inline during playbook run with `--ask-vault-pass` or `--vault-password-file`
- Use `ansible-vault encrypt_string` to inline-encrypt a single variable value in a vars file
- Rotate vault password: decrypt all, re-encrypt with new password
- Never commit plaintext secrets — enforce vault usage in CI with a pre-commit hook
