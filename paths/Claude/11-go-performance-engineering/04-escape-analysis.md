# Escape analysis

**Theme:** **Stack allocation** disappears cheaply until values **escape** to the heap—invisible allocations aggregate under latency variance and GC churn.

Study `go build -gcflags=-m=` (verbosity tuned) sparingly—it is noisy training wheels. Pair compiler hints with **`alloc_objects` / heap profiles** corroborating real impact.

Contrast:

| Behaviour | Typical driver |
|-----------|----------------|
| Escapes to heap | Returned pointers to local variables, closures capturing locals by ref, interfaces boxing concrete values unnecessarily, variadic escapes, unintended API surface returning pointers broadly |

### LAB — “Go ownership” pressure

Shrink API surfaces returning **pointers vs values** thoughtfully; refactor hot paths leaking small structs repeatedly into heap—benchmark + profile deltas side-by-side.

### Checklist

- [ ] Micro changes justified by measurable delta—escape flags alone insufficient story.  
