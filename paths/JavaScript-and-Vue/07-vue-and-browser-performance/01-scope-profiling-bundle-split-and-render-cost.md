# Unit 1 — Scope: performance literacy (Vue + browser)

Mindset shift: from “the app loads” toward **measurable cost**: JS evaluation, layout, rendering, memory, repeated network.**

## Learning outcomes

- Chrome **Performance**, **Network**, **Memory**, **Vue DevTools** as regular tools — not demos.
- **Bundle economics**: oversized initial JS → code-splitting intuition, tree-shaking relevance, **`import()`** dynamic chunks.
- **Route-level lazy loading**: defer admin/analytics/heavy screens until needed.
- **Render efficiency**: large lists; avoid accidental O(n) work per keystroke; `computed` vs eager methods; stable keys.
- **Network**: duplicate inflight calls, chatty waterfalls, payload bloat — pair with **`06-*`** cancellation/batching habits.
- **Assets**: image weight, lazy images, format trade-offs (high level).
- **Memory**: listener leaks, retained component state, detached DOM — tie back to **`02-*`**, **`04-*`** (Vue lifecycle/teardown), and **`05-*`** (store/router long-lived listeners) as needed.

Ship evidence: before/after metrics (bundle size, main-thread time, request count) for `shop-spa/` changes.
