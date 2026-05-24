# Unit 1 — Scope: JavaScript fundamentals (why the runtime, not syntax bingo)

Mindset shift: from “syntax tricks” toward **executable mental model**.

## Learning outcomes

- **Scopes**: global, function, and block scopes; lexical environment; visibility across nested functions.
- **`var`, `let`, `const`** trade-offs; temporal dead-zone intuition for interviews.
- **Hoisting**: declarations vs bindings; declarations vs expressions; predict output before running.
- **Closures**: inner function retains outer bindings; encapsulation (“private”) without classes; misuse (leaks).
- **Prototypes**: lookup chain (`[[Prototype]]`); classical patterns vs ES classes as sugar; inheritance vs delegation.
- **Promises**: states; chaining; error propagation; migrating callback thinking.
- **`async` / `await`** as control-flow sugar over promises; pairing with **`try/catch`**.
- **Event loop sketch**: call stack, tasks (macrotasks), **microtasks** (promise jobs, `queueMicrotask`).
- **ES modules**: default vs named exports; folder layout (`api/`, `utils/`, `modules/`) before any framework.

Practice spine throughout this area (no Vue): **`frontend-lab/`** — plain `.js`, modules, deliberate exercises.
