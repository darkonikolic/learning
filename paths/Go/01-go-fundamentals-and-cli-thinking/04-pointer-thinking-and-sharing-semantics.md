# Unit 4 — Pointer semantics: ownership and sharing

## Learning outcome

You read **`&` (address-of)** and **`*` (indirection)** mechanically *and* architecturally—you know whether a function observes **aliases** versus **temporary copies**.

This is traditionally where programmers coming from interpreted-first stacks misunderstand Go.

Sketch:

```go
func UpdateUser(u *User) { … }
```

## Core ideas

- Passing `*User` shares identity of the backing struct with callers when they already possess a pointer; passing `User` duplicates bytes (note: structs containing pointers still share nested pointer targets—ownership stories compound).
- `UpdateUser` should make obvious **what it mutates**, what it forbids (`nil`), and what it returns (`error` discipline comes next formal unit but preview honesty here).

## Practice

Implement `UpdateUser(u *User)` (name fields however you wish). Invent two call-site patterns:

- one where mutation is visible afterward,
- one where programmers *think* mutation happened but accidentally passed **values** copied into temp pointers or similar footgun.

Demonstrate corrected pattern.

## Lab

Answer explicitly:

“Why might `UpdateUser(user)` apparently change nothing sometimes?” Narrate copying, pointer-to-temporary pitfalls, misuse of loops/range-variable addresses.

## Interview prompts

- stack vs heap hand-waving discouraged—focus on observable semantics first,
- “when do I expose `*User` as API versus return new value?” pragmatics.
