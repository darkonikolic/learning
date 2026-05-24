# Unit 3 — Context, cancellation & leak hunting lab

Start from `ctx := context.Background()` and layer:

```
WithTimeout
WithCancel
nested child contexts with shortened budgets
```

Explain propagation direction and common leak: goroutine ignoring `Done`.

## Deliverable

Find & fix a deliberate worker leak in a toy repo you craft—document “signal used to confirm leak gone” (goroutine profile, runtime metrics story, etc.).
