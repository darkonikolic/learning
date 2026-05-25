# Lab: Boundaries — Symfony E-Commerce Monolith

Spine project variant: Symfony monolith for an e-commerce platform. Apply the split decision framework from `01-when-to-split.md`.

---

## System Context

**Stack:** Symfony, single Postgres database, no queue yet, no cache layer.

**Team:** 3 backend developers. No dedicated DevOps. Deployments are manual and happen 2–3 times per week, coordinated across the team.

**Load:** 50,000 orders/month (~1,700/day, ~70/hour at peak). Product catalog: 80,000 SKUs. No significant read/write imbalance currently.

**Domains in the codebase** (all in one Symfony app, mixed namespacing):
- Product catalog: browse, search, pricing, categories
- Inventory: stock levels, reservations, restocking triggers
- Orders: cart, checkout, order state machine, fulfillment tracking
- Payments: charge, refund, payment method storage
- Notifications: email and SMS dispatch on order events
- User accounts: registration, login, profile, address book

**Schema (simplified):**

```
users                  — id, email, password_hash, created_at
addresses              — id, user_id, street, city, country
products               — id, sku, name, description, price, category_id
categories             — id, name, parent_id
inventory              — id, product_id, warehouse_id, quantity, reserved_qty
orders                 — id, user_id, status, total, created_at, fulfilled_at
order_items            — id, order_id, product_id, quantity, unit_price
payments               — id, order_id, provider, amount, status, provider_ref
notifications_log      — id, order_id, user_id, channel, template, sent_at
```

---

## Exercise 1: Map Data Ownership

For each table, answer:
- Which domain **writes** to this table?
- Which domains **read** from this table (and for what purpose)?
- Is there a **write conflict** — more than one domain writing to the same table?

Use this template:

| Table | Owned By (writes) | Read By | Write Conflict? |
|---|---|---|---|
| users | | | |
| addresses | | | |
| products | | | |
| categories | | | |
| inventory | | | |
| orders | | | |
| order_items | | | |
| payments | | | |
| notifications_log | | | |

**What to look for:** Tables written by more than one domain are coupling points. They are either poorly named (the domains are actually one domain) or they represent a seam problem that a split would need to resolve with events or API calls.

---

## Exercise 2: Apply the Decision Table

For each domain, evaluate against the split criteria from `01-when-to-split.md`:

| Domain | Independent Deploy Needed? | Different Scaling Req? | Different Team Owner? | Different Failure Blast Radius? | Different Compliance Scope? | Split Justified Now? |
|---|---|---|---|---|---|---|
| Product catalog | | | | | | |
| Inventory | | | | | | |
| Orders | | | | | | |
| Payments | | | | | | |
| Notifications | | | | | | |
| User accounts | | | | | | |

**Fill in Yes/No/Partial with a one-line justification per cell.** The final column should follow from the others — not from intuition about what "feels" like a service.

---

## Exercise 3: Design the Modular Monolith

Before any service split, the first architectural move is making the module boundaries explicit inside the monolith.

Design the internal module structure:

1. Name the modules (map the 6 domains to 4–6 modules — some may merge)
2. For each module, define what it **owns** (its tables, its write path)
3. Define what it **exposes** to other modules (public interface: method calls, events, or read-only query objects)
4. Define what it **must not do** (the constraints: no direct cross-module table joins, no writing to another module's tables)

**Format:**
```
Module: [Name]
Owns: [tables]
Exposes: [interface description]
Must not: [constraint list]
```

**Aim for 4–6 modules.** If you end up with 6 modules that mirror the 6 domains exactly, ask whether any two modules are so tightly coupled that splitting them creates more interface overhead than value.

---

## Exercise 4: The One Split You Would Make First

Given:
- 3 developers, shared on-call
- 50k orders/month
- Manual deployments, 2–3x/week
- No queue, no cache

Name **one domain** you would extract to a separate service if forced to split today. Apply the decision table explicitly — write one sentence per criterion.

Then answer: what changes to team process are required before this split makes sense? (Deployment pipeline, monitoring, on-call rotation.)

---

## Exercise 5: The Split You Would Not Make Yet

Name **one domain** that looks like a natural microservice candidate but should stay in the monolith for now. Explain:
- What makes it tempting to split
- What makes it premature given the current team/load/ops context
- What condition would change your answer

---

## Example Answer: Exercise 4

**Domain to extract first: Payments**

| Criterion | Assessment |
|---|---|
| Independent deployment needed | Partial — payment provider integrations change on their own schedule, but currently there's no deploy velocity problem |
| Different scaling requirement | No — payment volume tracks order volume; no independent scaling gap |
| Different team ownership | No — same 3 developers own everything |
| Different failure blast radius | **Yes** — this is the strongest argument. A bug in notification dispatch should not cause payment processing to fail. A misconfigured Stripe webhook handler should not bring down checkout. |
| Different compliance scope | **Yes** — PCI DSS scope. Isolating payment card handling to one service reduces PCI audit surface across the rest of the system. |

**Verdict:** Two strong criteria met (failure isolation, compliance scope). This is the only domain in this system where both apply simultaneously.

**Pre-conditions before split:**
- CI/CD pipeline capable of independent deployments (not manual coordination)
- Monitoring and alerting on the payments service independently
- API contract defined between Orders and Payments (Orders places a payment intent, Payments processes it and emits an event)
- Decision on data: does Payments get its own Postgres schema/database, or is it isolated within the shared database first?

---

## Data Ownership Matrix — Reference

Use this to check your Exercise 1 work. Disputed cells are intentional — they reflect real coupling in most monoliths.

| Table | Most Likely Owner | Common Read-Crosses |
|---|---|---|
| users | User Accounts | Orders (billing), Notifications (recipient) |
| addresses | User Accounts | Orders (shipping address snapshot) |
| products | Product Catalog | Inventory (product_id FK), Orders (order_items) |
| categories | Product Catalog | Product Catalog only |
| inventory | Inventory | Orders (stock check at checkout) |
| orders | Orders | Payments (order_id FK), Notifications (order events) |
| order_items | Orders | Payments (amount verification) |
| payments | Payments | Orders (payment status display) |
| notifications_log | Notifications | Audit/reporting only |

**Note the coupling:** `inventory` is read by Orders during checkout. If you split Inventory, the stock-check at checkout becomes a synchronous API call or an eventual consistency problem. This is why Inventory is not the first split to make.
