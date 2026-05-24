# Unit 1 — Scope: Vue 3 core — component, reactivity, boundaries (no router, no Pinia)

**Prerequisite:** Comfortable reading `vue-tsc` diagnostics and keeping `defineProps` / `defineEmits` honest after **`03-*`**.

Mindset shift: from “template shows data” toward **state owns truth; template is a projection.**

## Learning outcomes

- **Component anatomy**: template / script / styles; when a file is too big (ownership split).
- **`ref` vs `reactive`**: primitives vs object graphs; unwrapping ergonomics in templates.
- **One-way data**: `defineProps` downward; immutability mindset for child inputs.
- **Upward intents**: `defineEmits` — parent retains authority over mutable truth.
- **`computed`**: derivation without shoving filters/maps into templates; caching semantics.
- **`watch`**: side effects tied to reactive sources; pairing with debounced search/async (later tied to **`06-*`** HTTP layer resilience).
- **Lifecycle**: mount vs unmount hooks; fetching on mount and **cleanup** (`onUnmounted`) to prevent leaks.
- **Boundaries**: dashboard → widget decomposition; cohesive ownership slices.
- **Reactivity internals (high level)**: Proxy-based dependency tracking → targeted re-render narratives.

Practice spine throughout: **`vue-lab/`** — **Vue 3 + Composition API only** until routing/Pinia arrives.
