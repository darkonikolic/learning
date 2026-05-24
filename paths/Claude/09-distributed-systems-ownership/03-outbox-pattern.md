# Outbox pattern

**Theme:** **Reliable causal bridge** DB → persisted intent → asynchronously published fact—without orphaned commits or phantom publishes.

Canonical mental wire:

```
DB transaction spans business mutation + outbox INSERT
    → dedicated relay/process polls / streams outbox safely
          → messaging broker absorbs with delivery semantics spelled out (e.g. at-least-once)
```

### LAB vector — Symfony payment → RabbitMQ

Design (or refactor toward) explicit **ownership**:

- transactional boundary includes outbox append  

- publisher never races ahead of commit visibility  

- consumer **idempotency hooks** keyed to business/domain ids  

Discuss duplicate publish, stalled relay backlog, reordering—all **outbox ownership** debt if ignored.

### Checklist

- [ ] Replay / compaction story for stale outbox rows without corrupting uniqueness constraints.  
