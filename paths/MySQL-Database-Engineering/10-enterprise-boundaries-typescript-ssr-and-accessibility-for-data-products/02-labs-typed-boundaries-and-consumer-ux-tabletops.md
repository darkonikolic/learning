# Unit 2 — Labs: typed seams + UX failure tabletops

Operate on a schema you already practise (ecommerce lab or smaller inventory subset). Use **safe** local/dev data only.

---

## Lab 1 — Generic repository boundary (TypeScript)

Implement a **narrow** repository interface for one aggregate (e.g. `Order`):

- `findById(id: BrandedOrderId): Promise<OrderRow | undefined>` using **branded IDs** (string literal brand) to stop cross-pollination with `CustomerId`.
- `listForUser(userId: UserId, page: PageCursor): Promise<OrderSummaryDto[]>` returning **DTO projections** (fewer columns than raw row type).
- Annotate where `readonly` on returned arrays prevents accidental in-place mutation leaking to UI stores.

Document one scenario where **GENERIC** default parameters would collapse inference if you mishandle `const` parameters.

---

## Lab 2 — Union + narrowing for order pipeline

Model `order_status` transitions as a **finite union** (`placed` → `paid` → `fulfilled` … + `cancelled` with reason). Build:

- Parser from **stringly** DB `ENUM`/`VARCHAR` column into the union.
- `assertNever` guarded reducer printing human-readable audit text.
- Unit tests showing illegal transitions **fail at type level** once you encode state machine as types (lightweight version acceptable).

---

## Lab 3 — Composition of DTO layers (no mega-type export)

Compose types using `Pick`, `Omit`, and intersection:

- `PaymentRow` (wide)
- `PaymentPublicDto` for external API responses
- `PaymentAdminDto` exposing operator metadata

Explain **why** shipping `PaymentRow` verbatim to SPA bundles is hostile to security posture + bundle size—even if HTTPS exists.

---

## Lab 4 — SSR / hydration narrative (desk exercise)

Assume an internal dashboard SSRs KPI numbers straight from nightly SQL rollup.

Write a memo covering:

1. Sources of divergence between SSR HTML totals and SPA-hydrated chart components.
2. How **replica lag** interacts with SSR if read traffic hits async replica pools.
3. Rollback playbook if hydrated UI throws—what happens to stale interactive shell?

_No need to ship full Node SSR stack—engineering memo + sequence diagram._

---

## Lab 5 — Accessibility audit on a data UI

Produce a **`Data-heavy admin`** screen (CLI HTML/prototype tolerated if you declare tooling):

1. Inspect heading order + landmark usage.
2. Verify sortable columns expose **meaningful announcements** OR explain why visuals alone fail WCAG-aligned expectations.
3. Run automated scan; classify each finding Severity vs Noise.

Deliverable includes **fixes** applied for at least two real issues discovered.

---

## Lab 6 — Cross-team contract incident

Fabricate changelog: `"orders.tax_cents"` nullable after migration; API neglected to update Zod/schema.

Produce **RCA**:

- Detection layer (monitoring/alerts/logs).
- TypeScript vs runtime validation interplay.
- User-visible symptom timeline.

Tie remediation to **backward-compatible API version** discipline.
