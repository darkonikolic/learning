# Architect Path

## Šta ovo gradi

Principal/staff architect nivo. Ne memorisanje — razumevanje dovoljno da znaš šta da pitaš i šta hoćeš.

Sa AI-jem ti ne trebaš detalje. Trebaš:
- Mentalni model koji prepoznaje pravi problem
- Vocabulary da komuniciraš precizno
- Decision framework za tradeoffe
- Komunikacijske veštine da odbraniš odluku

Svaki modul: decision table + anti-patterns + šta da pitaš AI + lab.

---

## Moduli

| # | Oblast | Problem koji rešava |
|---|--------|---------------------|
| 01 | `01-architect-thinking/` | Kako donositi odluke pod pritiskom, sa nepotpunim informacijama |
| 02 | `02-system-boundaries/` | Kada deliti sistem, kada ne — i kako to obrazložiti |
| 03 | `03-data-and-storage/` | Koji storage za koji problem; migracije bez downtime-a |
| 04 | `04-async-events-queues/` | Kada async, ko garantuje šta, kako ne izgubiti podatke |
| 05 | `05-reliability-failure/` | Kako sistem degraduje, SLO/SLI praktično, cascading failures |
| 06 | `06-scaling-performance/` | Bottleneck-first skaliranje, capacity math, caching kao odluka |
| 07 | `07-communication-decisions/` | ADR, stakeholder narrative, odbrana odluke pod pritiskom |
| 08 | `08-capstone-drills/` | 6 realnih scenarija + referenca šta da pitaš AI |
| 09 | `09-api-design/` | REST vs gRPC vs GraphQL, versioning, breaking changes, idempotency |
| 10 | `10-security-boundaries/` | Trust boundaries, auth/authz placement, secrets, audit log |
| 11 | `11-observability/` | Metrics/logs/traces kao arhitekturna odluka, SLO alerting |
| 12 | `12-deployment-architecture/` | Deployment strategije, DB migracije u deploymentu, rollback design |
| 13 | `13-network-layer/` | Load balancers, TLS termination, DNS, CDN — gde komponente stoje |
| 14 | `14-technology-evaluation/` | Framework za evaluaciju tehnologija, PoC dizajn, TCO |

**Redosled:** 01 → 02 → 03 → 04 → 05 → 06 → 07 → 09 → 10 → 11 → 12 → 13 → 14 → 08. Modul 08 (capstone drills) na kraju — ali `08/02-what-to-ask-ai.md` možeš koristiti odmah kao referencu. Moduli 01 i 07 su najvažniji.

---

## Referentni sistem

Spine kroz sve module: `Symfony API → Redis queue → Go worker → Postgres`

Primeri koriste ovaj stack. Ako radiš sa drugim stackom, principi su isti — zameni komponente.

---

## Kako koristiti

Svaki modul ima `01-*.md` (framework + decision tables) i `02-lab-*.md` (vežbe).

Radi labove. Arhitektura se uči kroz odluke, ne kroz čitanje. Kada naiđeš na pravi problem u radu, vrati se na relevantan modul kao referencu.

Modul 08 (`08-capstone-drills/02-what-to-ask-ai.md`) je referenca koju možeš koristiti odmah — pre nego što završiš ostale module.
