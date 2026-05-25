# Unit 1 — Module Scope: go-lab/ CLI

## What You Will Build

A single CLI codebase called `go-lab/` that grows across every unit. No HTTP, no frameworks — just Go structs, methods, interfaces, and packages. By the end of this module you will have a working CLI that manages Users, Products, and Orders, and a second small binary `task-cli/` that creates, lists, completes, and deletes tasks.

The point is not the CLI itself. The point is that you stop reasoning "Go as PHP classes with a different syntax" and start reasoning in Go's actual model: **structs hold data, methods attach behaviour to types, interfaces describe capabilities, errors are values, context carries cancellation.**

## Mental Model Shift

Coming from class-based languages, the instinct is to ask "what class does this belong to?" Go's question is different: "what type holds this data, and what behaviour does it need?" There is no inheritance, no constructor keyword, no `implements`. A type satisfies an interface simply by having the right methods. A zero value is valid until you decide it isn't.

This shift takes deliberate practice, not just reading. Build the code. Hit the edge cases. When something breaks, understand why.

## Module Goals (Checklist)

- [ ] Declare structs with exported and unexported fields; understand zero values
- [ ] Write value receivers (read) and pointer receivers (mutate); know when to use each
- [ ] Use `&` and `*` correctly; avoid nil pointer panics by guarding inputs
- [ ] Define and implement interfaces without an `implements` keyword
- [ ] Return and wrap errors as values; never use panic for normal error flow
- [ ] Organize code into packages with `cmd/` and `internal/` layout
- [ ] Initialize a module with `go mod init`; add and tidy dependencies
- [ ] Pass `context.Context` to functions that do slow or cancellable work
- [ ] Build capabilities through struct embedding, not inheritance
- [ ] Write table-driven tests with `go test ./...`

## Spine Project: go-lab/

Carry these types forward across all units — each unit adds behaviour to them:

- `User` — ID, name, email
- `Product` — ID, name, price, stock
- `Order` — ID, user ID, product ID, quantity
- `Cart` — items, totals

Capstone (Unit 11): `task-cli/` binary with `create`, `list`, `delete`, `complete` subcommands. Uses structs, interfaces, explicit packages, `go.mod`, and `context` on any simulated slow work.
