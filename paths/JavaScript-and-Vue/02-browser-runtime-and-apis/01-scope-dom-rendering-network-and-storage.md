# Unit 1 — Scope: browser as a runtime (not “HTML display”)

Mindset shift: from “I call DOM APIs” toward **rendering + network + storage + lifecycle** as a system.

## Learning outcomes

- **DOM as live tree**: query vs create vs mutate; cost of aggressive reflow/repaint.
- **Rendering pipeline** (conceptual): DOM + CSSOM → render tree → layout → paint → composite; when reflow vs repaint hurts.
- **Events**: listeners, bubbling vs capture, `stopPropagation` / `preventDefault` trade-offs.
- **`fetch`**: browser-side request lifecycle; loading / error UX hooks (even before Vue).
- **HTTP cache** in the browser: `Cache-Control`, validators (`ETag`, `Last-Modified`); hard vs normal refresh behaviour.
- **`localStorage` vs `sessionStorage`**: durability, tab scope, size and serialisation limits.
- **Memory**: detached DOM, forgotten listeners, growing caches — how leaks show up in DevTools.
- **Batching DOM work**: `DocumentFragment`, structural patterns to avoid 1k sequential hot-path updates.
- **DevTools**: Network, Performance, Memory — interpret slow requests, huge payloads, cache misses.

Practice spine: **`browser-lab/`** — still **no Vue**; plain JS against the real browser runtime. **Next** technical layer: **`03-*`** TypeScript discipline before framework work in **`04-*`**.
