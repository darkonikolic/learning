# Unit 2 — Labs (`browser-lab/` / `mini-shop/`)

## Exercises

- **Todo DOM**: add/remove tasks with explicit event wiring; deliberate stress test (`appendChild` in a tight loop) to feel layout cost.
- **Rendering lab**: tweak width/font-size; contrast batched DOM updates vs naive per-item mutation.
- **Nested buttons**: bubbling vs capturing; document when you’d stop propagation.
- **Fake e-commerce HTTP**: parallel `fetch` for users/products/orders + explicit loading/error states.
- **Cache lab**: inspect Network panel for validators and cache behaviour; articulate hard refresh vs warm cache.
- **Persistence**: cart survives reload via `localStorage`; justify storage choice vs `sessionStorage`.
- **Leak hunt**: detach nodes but keep listeners; observe retention; fixed version with teardown.

## Integration (`mini-shop/`)

Reuse DOM + `fetch` + storage + render narrative. Attach a short doc: **render flow** vs **network flow** vs **where state lives**.

Interview focus: DOM vs repaint/reflow, event propagation, fetch semantics, caching headers, storage choice, leak patterns.
