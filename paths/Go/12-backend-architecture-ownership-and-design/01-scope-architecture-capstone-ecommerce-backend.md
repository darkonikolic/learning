# Unit 1 — Scope: Refactoring to Layered Architecture

## What You Are Building

Take the working order system from Module 8 and refactor it into a properly layered e-commerce backend. By the end of this module you will have: domain types with business logic, a service layer that owns business rules, a repository layer for storage access, and an HTTP handler layer. No business logic in handlers. No HTTP types in services. No database imports in domain.

## The Four Layers

```
handler/          — HTTP only: parse request, call service, write response
  order_handler.go

service/          — business rules only: validation, orchestration, interfaces
  order_service.go
  interfaces.go   — repository and cache interfaces live here

domain/           — types and invariants only: no external imports
  order.go
  product.go

repository/       — database only: sqlx, SQL queries, row mapping
  postgres_order.go
  postgres_product.go
```

## Dependency Rules

```
handler   → service  ✓
handler   → domain   ✓
service   → domain   ✓
service   → repository interface (defined in service/)  ✓
repository → domain  ✓
repository → sqlx    ✓

handler   → repository  ✗  (skip the service — bypass business rules)
service   → handler     ✗  (upward dependency)
domain    → anything    ✗  (domain is the core — no external imports)
```

## What Each Unit Covers

| Unit | Topic | Deliverable |
|------|-------|-------------|
| 2 | Package naming | Audit and fix util soup |
| 3 | Layer discipline | Import graph verification |
| 4 | Manual DI | Wire everything in main() |
| 5 | Domain modeling | Order with behavior, not just data |

## What Success Looks Like

You can add a new business rule (orders over $1000 require manual review) by changing only `service/order_service.go`. The handler and repository do not change. The rule is testable with mocks — no DB required.
