# Ansible — `03-playbooks-tasks-and-modules`

**Focus:** Write playbooks that install packages, manage files, configure services — using the most common modules you will touch on every real job.

**Practise focus**

- Write a playbook that: installs nginx (`ansible.builtin.apt`), copies a config file (`ansible.builtin.copy`/`template`), and starts the service (`ansible.builtin.service`)
- Understand play structure: `hosts`, `become`, `vars`, `tasks`, `handlers`
- Use `handlers` for service restarts — trigger only on config change, not on every run
- Apply conditionals with `when`: skip a task if OS family is not Debian
- Loop over a list of packages with `loop` / `with_items`
- Register task output with `register` and use it in subsequent tasks
- Run playbook with `--check` (dry-run) and `--diff` to preview changes before applying
- Common modules to master: `apt`, `yum`, `copy`, `template`, `file`, `lineinfile`, `service`, `user`, `command`, `shell`
