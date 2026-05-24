# Retry + fallback ownership

**Theme:** Integrated toolchains fail mid-flight—ownership means **budgeted retries**, **tiered fallback**, articulated **human escalation—not infinite blind loops.**

### Canonical micro-pattern per failing hop

```
 ATTEMPT bounded tries (timeouts explicit)
                                              → classify FAILURE transient vs structural poison
                                                                              → FALLBACK degrade gracefully (narrower query slice, alternate data source sandbox, cached doc snapshot ethically)
                                                                              → ESCALATION human bridging when autonomy ceiling breached or risk spikes
                                                                              → DOCUMENT incident fingerprint for tooling reliability backlog honesty
```

**Practice tabletop failures**

**DB unreachable** transiently  

**Git** remote auth / flaky partial clone noise  

Synthetic **generic tool timeout / MCP stall**

Mandatory triad lab annotation after each rehearsed breakage:

Chosen **retry** posture & upper bound realism  

Chosen **fallback** narrative maintaining partial progress integrity  

Chosen **escalation** handshake preventing silent blockage theatre

Discuss **evaluation**: chronic retry inefficiency KPI surfaces unhealthy dependency flakiness—fix infra not only prompting.

### Checklist

- [ ] Fallback never bypasses approval escalations casually—narrowed scope ≠ permission elevation implicitly.  
