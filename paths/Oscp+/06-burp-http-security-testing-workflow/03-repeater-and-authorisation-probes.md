# Unit 03 — Repeater-driven HTTP manipulation

Continue Apprentice sections on **Repeater**.

Laboratory rehearsals (ethical targets only):

Adjust **Cookie**, **Authorization** headers, brittle numeric identifiers deliberately:

```http
GET /profile?id=SELF
→ GET /profile?id=SIBLING_SAFE_ID
GET /invoice/5 → GET /invoice/6    # authorised synthetic fixtures only
```

Map outcomes to hypothesis classes (authorisation leakage vs benign 404 distinctions).

Symfony targets locally: JWT minting endpoints, OAuth dance callbacks, coarse role segregation routes.

Themes: iterative tampering hygiene, duplication discipline, documenting unexpected successes **without leaking secrets externally**.
