# Unit 1 — Table-driven tests as an explicit design tool

Use **`tests := []struct{ … }{ … }`** to model dimensions of behaviour:

- `name string` becomes the subtest label—optimise failure readability.
- Prefer **focused fields** (`giveInput`, `want`, `wantErr`) over giant anonymous structs obscuring failures.
- `t.Parallel()` only when isolation is guaranteed—avoid shared mutable fixtures.

Deliverable: convert one formerly copy-pasted test file into tables + parallel policy notes.
