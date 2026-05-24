# Unit 2 — Labs: `ts-professional-lab/` (strict, generic, narrow, compose)

Work in a **strict** TypeScript project (Vite `library` template or `tsc --noEmit` + `tsx` runner). Each exercise ends with a **one-paragraph explanation**: what would have broken without the type, and what remains **unsound** at runtime.

---

## Lab A — Generics that survive refactors

Implement:

```typescript
function mapById<T extends { id: string }>(
  rows: readonly T[],
  selected: Iterable<string>,
): Map<string, T>;
```

- Accept **immutable** arrays; reject accidental widening of `selected` strings.
- Add overload or generic default so **callers infer `T`** from `rows`.

**Stretch:** second generic index signature safe access with `Record<string, T>` vs `Map` trade-off narrative.

---

## Lab B — Discriminated union + exhaustiveness

Model async API states:

```typescript
type Remote<T> =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'success'; data: T }
  | { status: 'error'; code: number; retryAfter?: number };
```

Write `function describe<T>(state: Remote<T>): string`:

- Exhaustive switch with **`assertNever` helper** trapping future variants.
- Unit-test that adding `{ status: 'stale'; data: T }` breaks compile until handled.

---

## Lab C — User-defined narrowing from JSON (`unknown` ingestion)

Given `unknown` payload from `fetch`:

1. Implement **type guards** `isProduct`, `isProductList`.
2. Pair with **`zod` or `valibot`** (either is fine)—compare ergonomic errors vs handwritten guards.
3. Document **difference** between compile-time certainty and runtime validation.

(This is the hinge into **`06-*`** where HTTP clients centralise.)

---

## Lab D — Composition > inheritance

Compose pricing rules using **pure functions + intersections**:

```typescript
type Money = { amount: number; currency: 'EUR' | 'USD' };
type Priced = { price: Money };
type DiscountRule = { kind: 'percent'; value: number } | { kind: 'fixed'; value: Money };
```

Build `applyDiscount(product: Priced & { rules: DiscountRule[] }): Money` **without classes**. Explain where **closed vs open extension** hurts you.

---

## Lab E — `satisfies` + `as const` configuration

Maintain a **`routes` table** keyed by literal path strings with metadata (`requiresAuth`). Use `as const satisfies Readonly<{…}>` to:

- Preserve literal keys for autocomplete.
- Forbid drifting optional flags silently.

Reflect: why `Record<string, …>` often **destroys inference** compared to **`satisfies`**.

---

## Lab F — Branded IDs (nominal-lite)

Implement **branded primitives**:

```typescript
type UserId = string & { readonly __brand: 'UserId' };
```

Functions `parseUserId(raw: string): UserId | null` vs unsafe cast—document phishing scenario where two stringly IDs collide conceptually.

---

## Lab G — Generic Vue SFC smoke (minimal)

Create **two** `.vue` files under `ts-professional-lab/vue-micro/`:

1. **`ListPanel.vue`**: generic `T` constrained to `{ title: string }`; props `items: T[]`, `renderKey: keyof T` (bonus: enforce `renderKey extends keyof T` properly).
2. **`ConfirmDialog.vue`**: typed emits `confirm`, `cancel` with void vs payload variants.

Ensure `vue-tsc` passes. Note every place you needed **`PropType`** or generic `defineComponent` escalation.

---

## Lab H — SSR / hydration tabletop (no mega framework required)

Write a short **scenario doc**:

- Express-style handler returns HTML with order total from REST.
- SPA hydrates summary card.
List **three plausible mismatch causes** and mitigations (`suppressHydrationWarning` is escape hatch — explain why masking symptoms is dangerous).

---

## Lab A11y micro-audit

Build a rudimentary **`DataTable.tsx` or Vue table** displaying mock rows:

- Wired header ↔ cell association (`scope`, or `thead`/`tbody` correctness).
- First focusable filter input on page load; **trap focus** in modal drill (even if mocked).
Run automated a11y pass; annotate **two** findings as false positives vs real defects.

---

## Interview drill bank (self-score)

Produce flash answers (≤45s verbal each):

1. Structural vs nominal with example.
2. Generic constraint vs overload when to prefer which.
3. Discriminant property naming pitfalls (`kind` collisions).
4. Difference between **`unknown`**, **`any`**, and **`never`** in catch cleanup.
5. Why `readonly T[]` parameters protect inference better than mutable arrays.
6. Hydration mismatch triage checklist (5 bullets).
