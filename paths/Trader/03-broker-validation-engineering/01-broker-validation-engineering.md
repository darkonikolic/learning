# Broker validation engineering — practise the operating layer

## Scope

Operational quality is not “which broker has the best banner ad.” It is **measurable**: spreads you pay, latency you feel under load, whether statements reconcile, exports parse, and whether drills exist before real outages.

Pairs naturally with `02-broker-platform-germany-operations` (selection, tax workflow themes). This unit is **measurement + rehearsal** on the stack you already chose.

## Core ideas

- **Expectancy hides in execution plumbing.** Quiet spread widening and occasional bad prints compound like any other recurring cost—log them deliberately.

- **Drills outperform hope.** Simulate outage and export recovery while calm; rehearsing hot loses money and sleep.

## Areas (with basic elaboration)

**Spread measurement**

- Sample bid–ask snapshots around your actual trade windows—not only midday calm. Log instrument, session slice, weekday vs rollover proximity.
- Separate **broker quoted spread** from **effective spread** paid on marketables when you deliberately cross.

**Latency measurement**

- Clock click-to-acknowledgement subjective tiers (platform UI responsiveness) versus objective order round-trip anecdotes where platform exposes timestamps.
- Note behaviour under news spikes—not only idle charts.

**Execution comparison**

- Compare execution artefacts across sessions and volatility buckets—rejects, partials, slippage versus plan—not only “feel.” Tag causes where you can distinguish platform vs liquidity vs impulse.

**Statement validation**

- Monthly reconciliation drills: blotter ↔ PDF/CSV statements; unmatched rows must close with an explanation recorded (corp action, FX rounding, odd fees, splits).

**Platform outage drills**

- Written path to flatten reduce or reconcile when UI fails mid-bracket; redundant path on second device where policy allows it; acknowledge phone-queue reality if API-only fails.

**Export validation**

- After broker UI upgrades, reopen your usual CSV columns and ingestion rules—a silent column rename breaks archives and adviser handoffs downstream.

**Mobile vs desktop workflow**

- Declare which workflows are forbidden on mobile (complex brackets, scaling ladders) versus allowed only (flatten, cancel all). Divergence breeds silent improvisation.

**Multi-monitor ergonomics**

- Stable screen layout anchors blotter latency clock news calendar journaling pane—reduces mis-clicks fatigued hours.

**Hotkey safety**

- Keep a numbered hotkey map; avoid ambiguous combos that flip market vs limit under stress; rehearse reversing a mistaken keystroke calmly.

## Common pitfalls

- Trusting promotional “spread from” screenshots instead of journaling **your** prints across weeks.

## Basic practice

- Broker **scorecard artefact**: three columns labelled **measure | method | acceptable band** spanning spread samples latency notes export parse success outage drill date.

## Outcomes / deliverables

One living **broker validation scorecard** plus one **outage drill checklist** exercised at least once on paper before you rely on adrenaline.
