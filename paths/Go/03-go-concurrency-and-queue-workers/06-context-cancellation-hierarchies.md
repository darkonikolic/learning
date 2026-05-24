# Unit 6 — Context cancellation hierarchies propagate termination intent

Patterns:

```go
ctx, cancel := context.WithCancel(parent)
defer cancel()
```

Interpret **parent ⇒ child ⇒ grandchildren** subgraph cancellation semantics when parent fire cancellation—downstream observes `Done` closures.

Contrasts mistaken mental model stacking detached `context.Background()` trees ignoring propagated coordination—enterprise Go begins structuring cross-service boundaries conscientiously—even if exercise limited locally first.

## Practice extensions

Enhance **`queue-worker/`** scaffolding: cancelling long faker jobs cooperatively—not merely killing goroutines brutishly.

## Mandatory reflection writing

Demonstrate cancelling propagates cleanly without lingering blocked senders mistakenly—coordinate channel closure thoughtfully.

## Interview prompts

**Always defer `cancel`** discipline reasoning.

Context misuse stuffing unrelated config overshadowing readability—disciplined restraint.
