# Unit 06 — Packages, logs, and systemd

## Theme

Keeping the system maintained and observable.

## LabEx

Finish:

- Package Management  
- Init / Systemd  
- Logging  

## Udemy — Linux Administration Bootcamp

Sections:

- `apt` (or distribution equivalent)  
- Logs  
- `journalctl`  

## Commands to practice

`apt`, `dpkg`, `journalctl`, `tail`, `tar -czf backup.tar.gz demo/`, `tar -xzf backup.tar.gz`

## Exercise

```bash
journalctl -xe
tail -100 /var/log/syslog
```

(Paths may differ by distro; adapt if you are not on Debian/Ubuntu.)

## Topic checklist

- Package management (`apt` / `dpkg` class)  
- Logs: `journalctl`, classic syslog files  
- systemd concepts tied to **enable/start/status**  
- Archives: `tar` + compression  

## Learning outcome

You can install/update packages, inspect recent system events, and create/restore a simple tarball backup of a practice directory.
