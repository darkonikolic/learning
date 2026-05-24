# Unit 2 — Struct thinking: Go is not your PHP object model

## Learning outcome

You model nouns primarily with **`struct`**, respecting **exported fields** versus **internal fields**, understanding **zero values**, and planning what “empty” means operationally—not magically “invalid until constructor runs” unless you deliberately enforce that elsewhere.

```go
type User struct {
	ID   int
	Name string
}
```

## Core ideas

- A struct is ordinary data aggregated by type—not a deity class with obligatory factories (though you *may* add factories when invariants demand it).
- **Zero value**: `var u User` assigns `ID == 0` and `Name == ""`. That is predictable; your job is deciding whether those values are legally meaningful for your bounded context.
- Uppercase/lowercase identifiers still define **exported vs package-private** APIs at the declaration site.

## Practice

Implement:

1. `User`
2. `Product`
3. `Order`

For each:

- Decide which fields tolerate zero values and where you will later forbid “half-built” aggregates (constructor function, validated builder, validation at command boundary).

## Lab (“why” narration)

Explain in prose why `var u User` succeeds and is usable whereas in many PHP OO habits you subconsciously expected an “object lifecycle” ritual first. Tie that to predictable memory/layout and idiomatic constructors **only when semantics require them**.

## Interview prompts

- struct layout intuition (ordering, alignment—high level okay),
- zero value guarantees,
- when zero is dangerous versus convenient,
- how you’ll tag for JSON/SQL later without polluting domain rules today.
