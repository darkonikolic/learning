# When to Split

The most expensive architectural mistake is splitting too early. The second most expensive is not splitting when you should have. Most teams make the first mistake.

---

## The Split Decision Table

Split when you have a concrete, present-day reason. Not a hypothetical future one.

| Condition | Justifies Split | Notes |
|---|---|---|
| Independent deployment required | Yes | Different teams need to ship without coordinating release windows |
| Different scaling requirements (proven, not projected) | Yes | One component is CPU-bound at 10x the rate of another |
| Different team ownership with explicit boundaries | Yes | Two product teams, two codebases, two on-call rotations |
| Different failure blast radius needed | Yes | Payments going down should not take the catalog down |
| Different compliance/security scope | Yes | PCI DSS scope creep is real and expensive — isolate it |
| "It's getting big" | No | Size is not a reason. Complexity inside a module is a reason. |
| "Microservices are what everyone does" | No | Social proof is not an architectural argument |
| "We might need to scale this later" | No | Scale when the load exists. Premature scaling is waste. |
| "This feels like a separate concern" | No | Separate concern → separate module, not separate service |
| "We want to use a different language/framework for this" | Weak | Tech diversity adds ops cost. Needs strong justification. |

---

## Monolith → Modular Monolith → Microservices

This is not a progression. It is a choice. Each point on the spectrum has a cost profile.

**Monolith**
- One deployment unit, one database, one process
- Ops cost: minimal — one thing to deploy, monitor, debug
- Team coordination: high coupling if modules not enforced at the code level
- Data consistency: trivially strong — everything in one transaction
- Debugging: stack traces are complete, no distributed tracing needed
- Right for: teams under 10 engineers, domains not yet well understood, early products

**Modular Monolith**
- One deployment unit, one (or few) databases, enforced internal module boundaries
- Ops cost: minimal — still one deployment
- Team coordination: modules give teams ownership without service overhead
- Data consistency: strong — still in-process, but modules don't share each other's tables directly
- Debugging: still simple
- Right for: most systems. This is the under-used option. It gives 80% of the organizational benefit of microservices at 20% of the ops cost.

**Microservices**
- N deployment units, N databases, N on-call rotations
- Ops cost: high — service mesh, distributed tracing, circuit breakers, retry budgets, schema registries
- Team coordination: explicit API contracts required, versioning required
- Data consistency: eventual by default — distributed transactions (saga, 2PC) are painful
- Debugging: requires correlation IDs, centralized logging, distributed tracing from day one
- Right for: large orgs with well-understood domain boundaries, independent team deployment velocity is the primary constraint

---

## Conway's Law, Practically

> Organizations design systems that mirror their communication structures.

This is not a suggestion. It is an observation about what will happen whether you plan for it or not.

If you want a service boundary between Orders and Payments, you need a team boundary between Orders and Payments. If both are owned by one team, the boundary will erode. Shared standups, shared backlogs, and convenience couplings will do it.

**What this means in practice:**
- Don't design service boundaries that your org chart can't support
- If you're a 4-person backend team, you do not have the team topology for 8 microservices
- If you want the technical boundary, first establish the organizational boundary (separate squad, separate roadmap, separate PagerDuty rotation)
- The inverse is also true: if two teams are sharing one service, expect that service to become two services eventually, whether you plan it or not

---

## Seam Identification

How to find natural split points in an existing system:

**Data ownership**: Which tables does each domain write to? If Domain A writes to Domain B's tables, they are not separate domains — they are one domain with confusing naming. A seam exists where a domain owns its writes and other domains can only read through an API or event.

**Transaction boundaries**: Where do your database transactions end? If paying for an order and reserving inventory are in the same transaction, splitting them requires a saga. That is real complexity. Find where transactions don't cross.

**Deployment frequency**: Which parts of the system change together? If Catalog and Orders are always deployed together because they share code, they aren't a natural split. If Notifications has never caused a revert of an Orders deploy, it has a natural boundary.

**Team ownership**: Who is on-call for what? Where is the blame game when something breaks? Natural ownership lines are natural service lines.

**Failure characteristics**: Which components crash independently today? Which bring each other down? A component that crashes alone and recovers alone is a candidate for extraction. A component that always takes 3 other things with it when it fails is deeply coupled.

---

## The Modular Monolith as a Final Answer

A modular monolith is not a stepping stone. For many systems, for years, it is the correct architecture.

Symfony's module system, bounded contexts enforced through namespacing and explicit interfaces between modules, a single Postgres database where modules own their schema but don't query each other's tables directly — this gives you:

- Independent development and testing of modules
- Clear ownership and blast radius control in the codebase
- The ability to extract a module to a service later, when you have the operational maturity and team structure to support it
- None of the distributed systems tax in the meantime

The question is not "will we eventually need microservices?" The question is "do we need microservices now, given our team size, load, and failure isolation requirements?"

---

## Decision Table: Team/Load → Architecture

| Team Size | Monthly Deploys | Scaling Gap Between Components | Failure Isolation Needed | Recommendation |
|---|---|---|---|---|
| < 6 engineers | Any | None proven | No | Monolith |
| < 6 engineers | Any | None proven | Yes (e.g. payments) | Modular monolith |
| 6–20 engineers | < 20/month | None proven | Partial | Modular monolith |
| 6–20 engineers | > 20/month | Proven on 1–2 domains | Yes | Modular monolith + 1–2 extracted services |
| > 20 engineers | High | Multiple proven gaps | Yes, per domain | Microservices where justified |

---

## Anti-Patterns

**Splitting by technical layer, not domain.** `AuthService`, `NotificationService`, `EmailService` are not domain services — they are infrastructure concerns. They cross-cut every feature. Splitting them creates circular dependencies or creates a god-service that calls everything.

**Microservices with a shared database.** If two "services" write to the same database schema, you have a distributed monolith: you got all the ops cost of microservices and none of the isolation benefits. Schema changes are still coordinated. Transactions still cross service boundaries. Deployments are still coupled.

**Splitting before understanding domain boundaries.** You find domain boundaries by running the system and watching where the seams appear. If you've been operating the system for six months and you still don't know which team owns the Order entity, splitting will not clarify that. It will just make the confusion more expensive.

---

## Šta da pitaš AI

These prompts produce useful analysis. Paste your actual system context where indicated.

- "We have [describe system: main entities, who writes to what, team structure, current load]. Which parts have independent scaling requirements? Which have different failure blast radii? List the ones that justify splitting and the ones that don't."

- "Draw the data ownership boundaries in this system: [paste schema or entity list]. Which entities are exclusively written by one domain? Which are written by multiple domains? Where are the shared write conflicts?"

- "If we had to split this system in 6 months, where would the natural seams be given this team structure: [describe teams, ownership, on-call]? What organizational changes would need to happen before the technical split?"

- "We are considering splitting [component] into its own service. Apply the split decision criteria: independent deployment need, scaling gap, team ownership boundary, failure isolation, compliance scope. What is the case for and against?"
