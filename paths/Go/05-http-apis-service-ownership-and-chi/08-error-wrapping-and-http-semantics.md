# Unit 8 — Error wrapping + purposeful HTTP semantics (no silent bubbling)

Practice pattern emphasis:

```go
fmt.Errorf("create order: %w", err)
```

Then boundary translation mapping internal errors selectively:

```
domain/repository distinctions → sanitized external API errors
versus diagnostic logging enriching internal-only detail fields
```

## Anti-pattern spotlight

Returning raw sentinel strings upward unclassified—observer teams cannot categorize retry vs permanent failure cleanly.

Produce mini internal taxonomy—even if handwritten constants initially—staging future `errors.Is` adoption consciously.

Interview expectation: reconcile **explicit errors** bridging earlier fundamentals Area 01 with transport mapping discipline now.
