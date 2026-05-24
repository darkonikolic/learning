# Broker / platform / Germany operations overview

## Scope

Build the **operational layer** around your trading: custody, statements, reconciliation, archiving, FX and fee visibility, reporting discipline.

Measurement drills (spread/latency/exports/outage rehearsals) belong in **`03-broker-validation-engineering`**; this chapter stays frameworks and workflows—not raw bench tests alone. This is boring infrastructure—until audits, outages, broker changes, or tax prep prove it mandatory.

Anything below marked **Germany** is **study scaffolding** for workflows you confirm with authoritative sources and a **tax professional (Steuerberater)**—not legal facts frozen in Markdown.

## Core ideas

- **Your archive is inventory.** If broker UI changes tomorrow, immutable exports dated by tax year survive.
- **Fees are expectancy.** Commissions + spread + swaps + dividend handling + FX markup belong in expectancy math and reviews.
- **Regulation sets guardrails.** Product access (retail CFD rules, PRIIPs, leverage caps, investor warnings) differs by geography—verify continuously.

## Areas (with basic elaboration)

**Selection & tooling**

- **Broker selection framework** — product coverage, segregation/protection disclosures, outages history, stability of exports, jurisdiction and compensation schemes (study official docs).
- **Platform comparison** — charting vs execution fidelity; journaling hooks; portability of history; scripting if you automate journaling.
- **Execution quality cues** — requotes/rejects routing transparency; outage playbooks—how you flatten or hedge when platform fails.

**Regulation basics (themes to verify)**

- **Regulation primer** — who supervises whom, segregated accounts language, suitability/knowledge tests where applicable—not one paragraph “answer.”

**Germany-oriented operations (confirm with advisor)**

- **Tax overview thematic** — when trading income can touch Abgaben in ways that deserve planning; thresholds and classification are individual—avoid fixed numbers unless copied from dated official guidance tied to YOUR case.
- **Private vs Gewerblich / commercial patterns** — only an advisor maps habituality, intentions, ancillary income, bookkeeping depth.
- **Reporting obligations checklist** — which broker exports satisfy which filing lines historically; **annual refresh** mandatory.

**Workflows**

- **Trade export workflow** — schedule; checksum or hash optional; filenames with date range & broker id.
- **Documentation workflow** — ticket → blotter → reconciliation to monthly statement deltas.
- **Broker statements vs internal ledger** — treat mismatches as bugs until explained (corporate action, FX, delayed settlement).
- **Trade archive ownership** — who stores what, redundancy (offline copy), naming convention.
- **Compliance ownership calendar** — what you owe and when—even if outcome is “not applicable.”

**Structure & currency**

- **Account structure** — single vs multicurrency wallets; segregation of speculative vs investing journals if legally distinct in your posture (advisor).
- **Conversion awareness** — functional currency bookkeeping vs broker display currency traps.
- **Cost structure ledger** — every debit line categorized (execution, idle cash drag, borrowing, dividends tax withholding).

## Common pitfalls

- Trusting screenshots without **statement reconciliation**.
- Migrating brokers without frozen **prior-year artefacts**.
- Using third-party calculators for DE tax specifics without validating against **annual Finanzamt forms** counsel uses.

## Basic practice

- Run a **reconciliation dry run** spanning a full brokerage statement cycle: scheduled exports → internal blotter match → annotate FX rows and fee categories until gaps clear or are explained.
- Write a **broker switch playbook** listing artefacts to migrate before goodbye (fills, dividends, withholding, FX).

## Disclaimer

Treat tax and residency-specific rules as **living research** aided by counsel; keep a dated log when assumptions change.
