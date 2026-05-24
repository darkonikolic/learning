# Unit 5 — Monolith, modular monolith, microservices: when boundaries earn their complexity

| Shape | Wins | Taxes |
|-------|------|-------|
| Monolith | fast iteration, simpler deploy early | coupling hotspots if boundaries ignored |
| Modular monolith (bounded contexts in one deployable) | domain clarity without network partitions | requires strict module rules & reviews |
| Microservices (only when triggers exist) | selective isolation of blast radius / scaling axes | contracts, observability, deploy complexity multiply |

## Practice

Annotate candidate seams in a Symfony-style monolith (`order`, `billing`, `user`, `notification`). For each candidate extraction to a separate service, list **what you buy** and **what you pay** (ops, data consistency, latency).

## Interview drill

What **organisational or technical trigger** would make you accept distributed transactions / sagas instead of pretending one SQL transaction saves you?
