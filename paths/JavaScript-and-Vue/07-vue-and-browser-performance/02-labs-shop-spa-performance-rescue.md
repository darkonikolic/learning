# Unit 2 — Labs: performance rescue (`shop-spa/`)

## Scenario stack (can be staged or combined)

- **Large list**: ~1k product rows — profile unnecessary re-renders; fix with derived state and structural discipline.
- **Fat bundle**: introduce then remove bloat — measure pre/post **route-level** `import()`.
- **Lazy routes**: admin / analytics / profile segments load only when visited; verify in Network.
- **Payload / duplicate calls**: reconcile double-fetch patterns; tighten API usage.
- **Images**: optimise product thumbnails; observe transfer size change.
- **Memory**: reproduce listener or store retention leak → fix with teardown.

## Deliverable

One-page memo: bottleneck → measurement → mitigation → residual risk/trade-off (e.g. “virtualisation deferred”).

Interview list: lazy loading, code-splitting, profiling, rerender hotspots, Lighthouse limitations, leak diagnosis.
