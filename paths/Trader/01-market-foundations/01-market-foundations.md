# Market foundations — what you actually trade

## Scope

Understand the instruments, liquidity, sessions, and order mechanics that sit *underneath* charts and indicators. Without this layer, execution quality and risk models are guesses.

Positional framing: **trading engineering / execution literacy**, not “predict the tape.”

## Core ideas

- **Different products = different constraint surfaces.** Stocks, leveraged FX rollover products, and futures each reshape fills, gaps, financing, halts, and reporting—even when candles superficially rhyme.
- **Price is negotiated in an auction.** Spread, displayed depth, time of session, scheduled shocks change *who* clears your exposure and at what cost.
- **Microstructure leaks into P&L.** Slippage and partial fills belong in expectancy—not a footnote labelled luck.

## Areas (with basic elaboration)

**Instrument families**

- **Single-name equities** — Halts, corporate actions (splits/dividends), exchange microstructure, extended-hours behaviour—expanded in **equities specifics** below.
- **ETFs** — Tracking error; NAV versus last trade premium/discount; liquidity interplay with underlying baskets.
- **Forex spot/roll synthetics via broker products** — Quoting conventions, funding accruals, jurisdictional quirks—expanded in **forex specifics** below.
- **Futures** — Expiry ladders, margins, ticks, curve behaviour distinct from CFD spot metaphors sharing chart skins.
- **CFDs where applicable** — Counterparty disclosures, PRIIPs/leverage safeguards by domicile, financing schedules—study *your* schedule not internet clichés.

**Spot versus derivatives framing**

Spot vocabulary often masks embedded financing/leverage through broker wrappers—read contract-level behaviour not marketing labels.

**Liquidity and friction**

Liquidity regimes, dynamic spreads, volatility clustering, sizing interactions with margin calls—foundation for downstream risk modules.

**Sessions and actors**

Who supplies liquidity versus consumes it shifts intraday—coarse realism beats conspiracy theories.

**Execution literacy**

Orders, queues, fragmentation where relevant, retail disconnect drill themes—paired later with Broker Validation Engineering for measurement discipline.

---

## Forex specifics — funding, windows, and cross-links to equities sleeves

Operational FX literacy is **ownership of recurring costs**, **event windows**, and **how FX states bleed into equities risk** when you genuinely mix sleeves.

### Carry and funding path

- **Carry-trade awareness** — Interest differentials accrue subtly relative to leveraged spot noise while regime shocks can erase months of clipping quickly—carry is contextual, never automatic income.
- **Swap ownership** — Sign and magnitude belong next to journaling rows or blotter summaries; burying swaps poisons expectancy and tax attribution hygiene.
- **Rollover mechanics** — Understand broker cutoff for crediting rolls, correlated spread spikes, ambiguity around “still same UTC day”—misalignment scrambles sequencing stories between gap risk and staged exits.

### Policy and scheduled shock

- **Economic-release handling** — Freeze rules, widen-only ladders, size-down ladders decided cold before red folders appear on calendars; tag executions with release-context metadata for later stats hygiene.
- **Central bank posture awareness** — Coarse familiarity with hawkish versus dovish drifts matters because **yield differentials reposition FX** even when discretionary thesis is tactical—prediction optional but hazard signalling mandatory.

### Cross-market scaffolding

- **Yield-differential intuition** — Carry math is scaffolding; realised paths often move on repositioning shocks and liquidity droughts—not only tidy interest gaps on a spreadsheet.

- **US dollar index (DXY) as context** — It is an artificial basket—not your traded pair—and correlations with risk assets fracture in stress; use it sparingly as **tone**, not deterministic oracle linkage.

### Pair-selection discipline

- **Major versus minor crosses** — Tighter majors often show different liquidity and news beta than minors or exotics; define which families you deliberately trade—and which you forbid when spreads blow out unpredictably versus your journaling history.

### Correlation map (lightweight operational)

- Maintain a qualitative **overlap map** bridging FX exposures you hold or hedge implicitly against equity factor tilts—for example exporters versus strong-USD regimes—so macro shocks cannot surprise you stacking invisible correlated bets blindly.

---

## Equities specifics — gaps, corp actions, and session edges

Thin coverage if you purely trade ETFs or indices—but **single-name** reality hits fast without these rails.

### Earnings-led gaps

- **Earnings-gap awareness** — After-hours headlines reopen prices far from the prior cash close; declare beforehand whether setups **participate, throttle size, or avoid** earnings windows—not amid headline dopamine.

### Corporate actions

- **Splits** — Quantity and nominal price mechanically adjust across vendor charts versus broker rows on mismatched timelines; reconcile so expectancy work does not show fake gains/losses.

- **Dividends** — Ex-div cash timing, withholding, adjustment conventions for charts, and bookkeeping/tax overlays belong explicitly mapped (**verify with advisers**).

### Halts & venue stress

- **Market halts** — Pauses scramble intraday liquidation planning; playbook states halt policy (auto-disqualify symbol, escalate manual review tiers, etc.).

### Session extensions

- **Premarket / post-market** — Thinner liquidity, wider spreads, different order handling; forbid or selectively permit by playbook—with journaling tags distinguishing **cash vs extended** sessions.

---

## Common pitfalls

- Marketing-grade **FX leverage** versus survivable clustered volatility paths—not the same universe.

- **Chart-only equities** narratives while ignoring corp actions splits dividends halts rewriting live risk mechanically silently.

## Basic practice

- Extend your trade memo with forex lines: rollover cutoffs, documented swap polarity, majors/minors policy, macro-release throttle behaviour, discretionary USD-tone context discipline.

- Add equities operational lines: earnings stance, split/div reconciliation checkpoint, halt policy snippet, extended-hours allowed/forbidden tagging.

## Outcomes / deliverables

- One-page glossary bridging **instrument → risk surface → session → funding → corp actions**.

- Lightweight **cross-sleeve correlation sketch** tying USD tone plus equity factor tilts you actually hold—honest scribble beats mythical diversification stories.