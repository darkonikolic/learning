# Unit 4 — Memory model interview: slices, maps, capacity, retention

Explain:

```go
s := make([]int, 0, 100) // capacity vs length semantics
```

Discuss map growth, pointer semantics in map values (struct vs pointer values) at high level, and accidental slice backing array retention.

## Deliverable

Three oral explanations (record notes) connecting **stack vs heap intuition** to evidence (escape logs / profiles) without myths.
