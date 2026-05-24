# Risk : reward engineering — measuring quality not hype

## Scope

Separate **statistical merit** from **storytelling**: risk multiples, payoff asymmetry, expectancy, distribution shape. Winning trades neither prove excellence nor disprove a broken process.

## Core ideas

- **Expectancy is an average over trades**—silent about streak length and pathology of worst outcomes.
- **Win rate is trade space** versus **payoff asymmetry**; extremes can coexist in sustainable systems—or mask overfitting briefly.
- **Quality metrics must align with how you Journal & tag** setups; orphaned trades poison statistics.

## Areas (with basic elaboration)

**Ratios**

- **Risk : reward (R:R)** — planned multiples vs empirical distribution of realised multiples (often uglier).

**Expectancy**

- **Positive expectancy formulation** — (win% × avg win) − (loss% × avg loss), extended with costs and partial fills—not chart fantasy.
- **Expectancy sensitivities** — how fragile expectancy is when win rate dips 5 points or payoff skew compresses—sanity modelling.

**Trade-offs**

- **Win-rate ↔ payoff asymmetry** — accepting lower win-rate for asymmetric payoffs shifts psychological load; plan psyche budget too.

**Diagnostics**

- **Profit factor** — gross wins / gross losses; brittle with small samples; useful trend warning when journaling deep.
- **Edge measurement pipelines** — compare tagged subsets vs naive baseline subsets (avoid self-serving slicing).
- **Payoff distributions** — skew concentration: many small winners / rare large losers or inverse—each dictates risk engineering.

**Averages**

- **Average win / average loss sanity** — check fat tails—not only means.

**Sustainability**

- **System sustainability narratives** — can drawdown amplitude still exist within capital runway & psychology budget?
- **Variance awareness** — confidence intervals widen with path length; humility tables matter more than headline expectancy.

## Common pitfalls

- Declaring expectancy after **<30–50 homogeneous trades** tagged identically—but even then remain sceptical depending on rarity.
- Excluding worst trades as **“mistakes Outlier”** when pattern recurringly signals playbook flaw versus discipline flaw—disambiguate ruthlessly.

## Basic practice

- Build rolling stats view: expectancy, payoff ratio by **single playbook**, streak lengths, longest adverse excursion aggregates (even approximate).
- Every month annotate **why metrics moved** versus random noise hypotheses.

## Outcomes / deliverables

Rolling stats artefact keyed to **labeled trade sets**.
