# Unit 1 — Scope: TypeScript at professional depth (before Vue + HTTP hardening)

You already own JavaScript execution semantics (**`01-*`**) and the browser runtime (**`02-*`**). This block upgrades you to the **type discipline** expected in senior Vue + API codebases: composable abstractions, safe narrowing, generics that survive refactors, and mental models sharp enough that `lang="ts"` is an asset—not a tarpit of `any`.

---

## Architectural outcomes

### 1. Structural typing vs nominal habits

TypeScript compares **shape**, not nominal class names—except for intersections with private fields / branded types hacks. Interview articulation:

- Widening literal `const x = 'ok'` to `string` when reassigned across boundaries.
- **Excess property checking** only on fresh object literals—not on aliased bindings.
- **Readonly** differences vs mutable arrays/objects in inference.

Deliverable intuition: explain *why* two interfaces with identical fields unify in assignment even if “conceptually different business entities” unless you deliberately **brand**.

### 2. Compiler flags & production posture

Operate with **strict-family** semantics in mind (`strict`, `strictNullChecks`, `noUncheckedIndexedAccess` trade-offs, `exactOptionalPropertyTypes` footguns optional). Understand:

- `undefined` in optional props vs omitted keys when exact optional is on.
- **Non-null assertions (`!`)** as debt you must justify—not a default linter escape.

### 3. Generics beyond syntax sugar

Professionals weaponise generics because **API boundaries move**:

- Constraints: `T extends Identifiable`, `T extends keyof SomeMap`, recursive constraints for tree-shaped JSON.
- **Multiple type parameters** with sensible defaults (`TData = unknown`).
- Inference sites: helper functions preserving unions vs accidentally widening.
- Variance intuition (arrays are invariant in mutation positions; **`Readonly<T>`** loosens covariance stories for callbacks—enough depth to avoid bogus “contravariant” hand-waving).

### 4. Union types & discriminated unions

- Narrowing primitives: `string | number` with `typeof`.
- **`kind` discriminants**: exhaustiveness checks via `never` reducer or `switch (x.kind)` with `assertNever`.
- **Optional chaining + nullish coalescing** integrated with `strictNullChecks` mental model.

### 5. Composition patterns (not “OOP theatre”)

- Intersection types `A & B` vs union `A | B` for layering DTOs.
- Mapped types teaser: `Pick`, `Omit`, `Partial`, `Required`, `Record`—implemented understanding, not only imports from `utility-types`.
- **Composition helpers**: small pure functions lifted through generics instead of fragile inheritance hierarchies.

### 6. Narrowing ergonomics (`as const`, `satisfies`, predicates)

- `as const` for literal widening prevention + tuple preservation.
- **`satisfies` operator**: keep inference while asserting compatible shape (`satisfies SomeConfig`).
- **User-defined type guards** returning `value is Foo` justified by runtime validation (paired with **`06-*`** when HTTP JSON arrives).

### 7. Module graph & ambient types

Know when `.d.ts` augments globals vs when **`import type`** keeps emitted JS clean (`verbatimModuleSyntax` awareness). Respect **triple-slash** rarity—prefer modular imports.

### 8. Error modelling as typed data (`Result` ergonomics pattern)

Professionals unify failure paths:

- Lightweight `Ok | Err` union with discriminant vs throwing across async boundaries—trade-offs with Vue/Pinia ergonomics discussed in **`06-*`**.
- Narrowing failures without `catch (e: any)`.

---

## SSR & hydration — conceptual backbone (engineering interview depth)

Separate **SSR** (initial HTML snapshot produced on a server) from **CSR-only** SPAs.

- **Why DB-backed dashboards** often mix SSR: faster first meaningful paint, SEO for product surfaces, consistent auth gating at the edge.
- **Hydration**: client runtime reattaches event listeners + reuses DOM; **mismatch** when server HTML ≠ client virtual tree (common causes: random IDs, locale/timezone drift, `Date.now()` in render path, feature flags diverging per host).
- **Partial hydration / islands** as complexity trade-off—name the idea even if you do not implement a framework.

Link forward: production cache + security around tokens during SSR discussed in **`09-*`**.

---

## Accessibility (a11y) — minimum professional bar

You are not becoming a WCAG auditor here; you **own** the engineering basics that stop “pretty but unusable” data UIs:

- **Semantic landmarks** (`main`, `nav`, headings hierarchy) for screen-reader wayfinding.
- **Keyboard operability**: focus order, `tabindex` discipline, escape / enter patterns in dialogs.
- **Focus management** on SPA route changes (announce page context when reasonable).
- **Colour contrast & motion** awareness at spec level (where to look, not every SC number).
- Tooling: **Accessibility tree** in DevTools + one automated pass (axe / Lighthouse a11y) interpreted critically (false negatives/positives).

Forward link: component tests can assert **roles + labels** in **`08-*`**.

---

## Vue 3 + TypeScript — what you must preload

Before **`04-*`**:

- `<script setup lang="ts">` inference for `defineProps` / `defineEmits` with **generic components** patterns.
- `PropType` vs direct generic `defineProps<{ id: string }>()` ergonomics.
- **Ref / reactive** generic parameters; unwrapping in templates vs script (where inference stops).
- **Event payload typing**—no silent `any` on `$emit`.
- `withDefaults` for optional props + TypeScript interplay.

You will still practise raw components in **`04-*`**; this block front-loads the **type muscle** so you do not fight the compiler while learning reactivity.

---

## Practice spine

Maintain **`ts-professional-lab/`**: small packages or Vite library apps (no full design system) where you can compile with strict settings and iterate fast.

Do **not** embed full Vue here beyond micro-SFC smoke tests when the lab demands—**`04-*`** owns component architecture depth.
