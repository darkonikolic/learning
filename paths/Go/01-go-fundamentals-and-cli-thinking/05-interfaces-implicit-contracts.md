# Unit 5 — Interfaces: behavioural contracts without inheritance drama

## Learning outcome

You treat interfaces as descriptions of capabilities—**often tiny**—rather than hierarchies proclaiming ontology.

Starter shape:

```go
type Logger interface {
	Log(message string)
}
```

Implement independently:

- **`ConsoleLogger`**
- **`FileLogger`**

Inject them wherever domain actions need auditing—avoid global singletons early so later tests sting less.

## Why “small interfaces” win

Compose systems from replaceable collaborators. Oversized interfaces become mock-the-universe nightmares and hide unused contract corners.

Classic interview phrasebook item: **interface segregation** interpreted operationally—“don’t merge unrelated behaviours just because naming is convenient Tuesday morning.”

Implicit satisfaction means your concrete types declare **nothing** tying them to interfaces except actually implementing listed methods—that decouples packages.

## Practice

Route logging decisions through **`Logger`** so CLI actions can silence output, tee to stderr+file later, swap with `io.Writer` façade when you deem proper.

## Lab

Write rationale for narrowing `Logger`: what did you consciously **not** add (levels? structured fields?), and deferral rationale.

## Interview prompts

- implicit vs explicit implementations (Dart/Java contrast),
- when huge interface from stdlib emerges (`io.Reader`) vs when you forbid local mega-interfaces.
