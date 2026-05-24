# Alerting hygiene & burn rates

**Theme:** Alerts are **budget burn detectors**, not anxiety generators.

### Multi-window / multi-burn awareness (conceptual)

High-severity pages should correlate with **fast budget consumption**—study Google SRE alerting patterns conceptually even if tooling differs.

### Severity model alignment

Wire observability alerts to **`39`** incident severity vocabulary—avoid dual incompatible scales.

### Checklist

- [ ] paging alert count **bounded**—team can review monthly without fatigue  

- [ ] non-page «info» channel alerts still owned and triaged within SLA  

- [ ] runbook **one-liner** exists for every page route  
