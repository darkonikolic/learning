# Unit 1 — Scope: enterprise-facing boundaries around MySQL-backed products

Pure SQL literacy is not enough when data **leaves InnoDB** — it becomes JSON over HTTP, SSR HTML, or client state. This area tightens the **contract layer** so schema drift, ambiguous unions, inaccessible admin UIs, and hydration bugs do not undo diligence from earlier **MySQL worksheets** here (indexing **`03-*`** through **`09-*`** interview blocks).

---

## Learning outcomes

### TypeScript + MySQL row shapes (application discipline)

- Separate **row type** (exactly what `SELECT` returned) from **domain type** (what the business module may assume after validation).
- Generics for **repositories**: `Repository<TRow, TId>` with constraints `TRow extends { id: TId }` — articulate when generics buy safety vs ceremony.
- **Union + narrowing** for nullable columns, status `ENUM`s, soft-delete flags — never leave `string` as the dumping ground where a finite domain exists.
- Prefer **narrowing via validation** (`zod`/`valibot`/`typeguard`) at process boundaries—not blind casts from `mysql2` row arrays.

### Composition patterns crossing the DB boundary

- Build **pipes**: `mysql row → validated DTO → view model`; document where immutability and `readonly` help concurrent refactors across services.
- Avoid “god typings” that paste entire tables into SPA bundles—surface **minimal projections** typed explicitly.

### SSR & hydration — conceptual mastery for architects

- Explain **SSR** when dashboards or marketing surfaces must ship HTML with authoritative numbers from SQL.
- Understand **hydration**: client attaches behaviour to server-rendered markup; articulate root causes when IDs, timestamps, locale formatting, randomised marketing copy, or A/B flags diverge server vs browser.
- Name mitigations beyond `suppressHydrationWarning`: stabilise entropy sources, unify clock/locale negotiation, consolidate feature flags upstream.

### Accessibility for data-heavy UIs

- Heading hierarchy when tables represent nested entities.
- **`scope` semantics** vs ARIA-only shortcuts for sortable columns.
- Keyboard focus when inline editing cells or running dangerous SQL-adjacent actions (delete, refund) from admin panels.
- Focus management when modals confirm destructive operations.

### Enterprise interview articulation

You should whiteboard how **schema change** (new nullable column) propagates through **types**, **API version**, **SSR payload**, and **client cache** without hand-wavy “we’ll fix later”.

---

## Positioning inside this path

This is **not** a replacement for a dedicated frontend track — it is the **interface consciousness** every storage engineer working next to TypeScript services or Vue apps must own. Pair with **`paths/JavaScript-and-Vue/03-*`** if you need front toolkit depth; here the lens stays **data fidelity + consumer UX risk**.

---

## Deliverable mindset

Any exercise you finish should answer: **If the column lies, which layer catches it, and what does the user experience before engineering notices?**
