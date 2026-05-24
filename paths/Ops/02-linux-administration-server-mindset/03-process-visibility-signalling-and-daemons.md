# Unit 03 — Process visibility, signalling patterns, graceful versus abrupt termination

Comfortable ergonomics: `ps aux`, `top`, `htop`, `kill`, `killall`, job introspection (`jobs`), `bg`, `fg`.

## Guided lab

Spawn a deliberately long idle footprint:

```bash
sleep 500 &
```

Locate PID, validate characteristics in tooling, rehearse escalating signals — prefer cooperative shutdown pathways before abrupt escalation when ethically acceptable locally.

Articulate distinctions between systemd-supervised daemon lifecycles vs ephemeral shell-managed jobs disappearing on session collapse.
