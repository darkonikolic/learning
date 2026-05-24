# Unit 10 — Composition: inheritance intuition reframed deliberately

## Learning outcome

Rebuild **capabilities** assembling structs embedding collaborators / explicit fields instead of phantom inheritance hierarchies.

Construct:

```text
OrderService + Logger collaborator + injected Config abstraction
```

Clarify how PHP mental models tempt **deep derivation** stacks that obscure dependency directions.

## Embedding nuance checklist

Exported promoted methods readability vs surprise—discipline naming so promoted API surface remains intentional—not accidental shotgun.

## Practice

Wire `OrderService` constructor accepting collaborators via interfaces/concrete collaborators where justified.

Show **alternate composition** rewriting a hypothetical naive inheritance doodle from PHP-think into idiomatic decomposition.

## Lab

Articulate succinctly inheritance advantages you surrendered consciously **and what Go compositional ergonomics reimbursed you** regarding testability/import clarity.

## Interview prompts

- embedding vs plain field trade-offs,
- when shallow embedding becomes API leak,
- mocking/service substitution via interfaces interplay preview (Area `09`),
- synergy with structs/receivers (Units 2–4).
