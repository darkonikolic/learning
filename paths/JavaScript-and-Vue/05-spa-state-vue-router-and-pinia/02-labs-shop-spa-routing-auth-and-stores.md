# Unit 2 — Labs (`shop-spa/`)

## Router

- Routes for `/`, `/products`, `/products/:id`, `/cart`, `/profile`, optional `/admin`.
- Param extraction and display; programmatic navigation exercises (e.g. after add-to-cart).

## Pinia

- Implement **cart**, **auth**, **products** stores with tight APIs.
- Refactor away from prop drilling; document anti-pattern you removed.

## Auth + guards

- Fake login; protect `/profile` and `/admin`; redirect with return URL if you want the stretch goal.

## Resilience (preview of **`06-*`**)

- Product list flow with explicit **loading / retry / error** surfaces for at least one API.

## Integration milestone

End state: multi-route SPA with **store ownership**, **route ownership**, **guards**, **persistent cart**, documented **why** each boundary exists.

Interview topics: Pinia vs local state, router guards, SPA vs MPA, persistence strategy, navigation flow.
