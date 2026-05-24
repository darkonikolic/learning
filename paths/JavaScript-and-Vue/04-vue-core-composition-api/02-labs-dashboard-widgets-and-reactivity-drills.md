# Unit 2 — Labs (`vue-lab/` / `dashboard/`)

## Guided builds

- **Cards**: `ProductCard`, `UserCard`, `NotificationCard` composing a realistic layout (header/sidebar/content) without dumping 1k-line “god components”.
- **Counters & reactive objects**: derive UI without manual DOM; explain why `count++` updates UI.
- **Props drill**: dashboard → list → leaf; forbid child mutating props; document data flow sentences.
- **Emit flows**: child raises `add-to-cart`; parent commits state mutations.
- **Computed**: totals, filtered lists; contrast with naive methods re-running every render.
- **Watchers**: search typing → debounced side effect (fake fetch placeholder).
- **Lifecycle**: load on mount, cancel/cleanup on unmount; introduce then fix a deliberate listener leak.
- **Reactivity deep-ish**: nested object changes should remain explainable with dependency tracking language.

## Integration (`dashboard/`)

Products, cart surface, notifications, stats — document **who owns which truth** and how events cross boundaries.

Interview topics: `ref` vs `reactive`, props vs emit, computed vs watch, lifecycle cleanup, component ownership, reactivity model at whiteboard depth.
