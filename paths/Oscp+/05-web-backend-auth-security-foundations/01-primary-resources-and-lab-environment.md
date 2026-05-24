# Phase four — Web, backend & auth security (resources & lab posture)

Objective: reproducibly articulate **attacks, mitigations**, and pragmatic **reviews** touching modern backends—not performing shallow exploit cosplay devoid of taxonomy.

Desired capability snapshot:

Reproduce cornerstone web vuln classes ethically in **local**/PortSwigger/authorized arenas

Articulate defenses & friction classes

Operate **Burp Proxy** thoughtfully

Comfortably discuss **JWT lifecycle pitfalls** without magical thinking

Interpret **OAuth** redirect & token handling failure families

Orient **API security & dependency/supply-chain** tooling stories

Honor **review mental model**, not leaderboard chasing alone.

## Core references

| Corpus | Purpose |
|--------|---------|
| [PortSwigger Web Security Academy](https://portswigger.net/web-security/getting-started) | Hands-on thematic labs spanning injection, SSRF, access control nuances, deserialization, JWT, OAuth, request smuggling intro, XSS family, CSRF, file path traversal & upload pitfalls, advanced optional edges |
| [OWASP Top 10 Project](https://owasp.org/www-project-top-ten/) | Category mapping fidelity |
| [OWASP API Security Top 10](https://owasp.org/API-Security/) | Backend API exposure reality |
| [Burp Suite](https://portswigger.net/burp) | interception / repeater ergonomics mastery |
| [Trivy](https://trivy.dev/) (image & dependency scanning illustrative) | container supply posture orientation |

Ethics: constrain traffic to sanctioned environments / personal builds / Academy targets.

## Local technical stack cues (adapt to your codebase)

Symfony project with realistic auth surfaces, JWT experiments, OAuth client/server flows consciously isolated, Dockerized dependencies, reproducible seeded data—not production secrets leakage.

Phase rule (each vulnerability class minimally):

Theory → Controlled attack rehearsal → Mitigation/defense rationale → Sanity pass on personal project surfaces if applicable.

Units `02–12` operationalize sequentially.
