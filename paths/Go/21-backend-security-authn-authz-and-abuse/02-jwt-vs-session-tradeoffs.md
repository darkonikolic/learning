# Unit 2 — JWT vs server-side sessions in API design

Compare trade-offs honestly:

| Approach | Strengths | Pitfalls |
|----------|-----------|----------|
| JWT (often short-lived access) | stateless verification at edge | key rotation, revocation stories, fat tokens, algorithm confusion class of bugs historically |
| Sessions (server store) | simpler revocation | scalability, sticky sessions smell, store availability |

Deliverable: verbal story for **logout**, **compromised token**, **key rotation** under each model.
