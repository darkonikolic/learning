# Unit 2 — Interface design interview lab: implicit satisfaction & segregation

Given:

```go
type Logger interface { Log(msg string) }
```

Explain implicit implementation, why **small** interfaces ease testing and composition.

Extend with `io.Reader` style reasoning: large interfaces are debt.

## Deliverable

Write **5 refactor scenarios** turning fat interfaces / concrete mega-structs into narrower seams without over-abstracting—justify each cut as if in staff review.
