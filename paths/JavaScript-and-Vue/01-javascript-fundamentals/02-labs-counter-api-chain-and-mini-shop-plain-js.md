# Unit 2 — Labs: drills + integration (`frontend-lab/`)

## Micro-drills

- **`counter.js`**: block vs function scope; explain what each nested block “sees.”
- **Hoisting puzzle**: contrast `sayHello()` with declaration vs `hello()` via `const`/expression; predict then run.
- **Closure toolkit**: counters, memoisation-style cache, guarding mutable state behind a narrow API.
- **Prototype sketch**: lightweight `User` → `Admin` chain; articulate where lookups stop.
- **Promise chain**: at least three steps with `.then`/`.catch`; surface rejected branch.
- **Async flow**: sequential fake **users → orders → payment** APIs with **`async`/`await`** and explicit error path.
- **Event-loop prediction**: mixes of `console.log`, `setTimeout`, `Promise.resolve()` — write order on paper before execution.

## Integration (`mini-shop/`)

Wire **modules**, **closures**, **async**, and **minimal state** inside cart / fake API flows. Document **why** an ordering or data boundary exists, not only what API you called.

Interview checklist from this phase: closures, prototype chain basics, promises & `async`, microtasks vs macrotasks, hoisting distinctions, **`let`/`const`/`var`**, module boundaries.
