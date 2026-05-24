# Unit 04 — systemd unit literacy plus correlated journalling ingestion

Operational verbs spanning enable/disable choreography, restrained `restart` vs `reload` where documentation differentiates behavioural impact on long-lived sockets.

Inspect aggregates:

```bash
journalctl -xe
journalctl -u ssh --since "15 min ago"
```

## Break-fix rehearsal ethical constraint

Stopping remoting daemons blindly risks lockout — coordinate safeguards (console access, ephemeral VM, reversible snapshots) beforehand.
