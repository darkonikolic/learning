# Unit 4 — Composer: reproducible graphs, autonomy, governance

## Outcomes

- **`composer.json` declares intent**, `composer.lock` pins reality—articulate rollback strategy when merges conflict on lock divergence.
- **Autoload semantics** (`psr-4` mapping discipline) aligning namespace roots with folder reality—prevent ghost directories.
- **Platform config** pinning PHP extensions—avoid surprises in CI parity.
- **Replace / path repos** sparingly document escape hatches risking supply-chain drift—when local override is ethically justified temporarily.

## Lab

Conduct an **upgrade rehearsal** sandbox:

```
composer outdated --direct
```

Pick one non-major bump. Document:

- breaking risk scan (changelog skim),
- test matrix delta,
- whether you’d batch or isolate release.

Interview: Discuss **supply chain vigilance**: integrity constraints, verifying sources, narrowing dependency fan-out intentionally.
