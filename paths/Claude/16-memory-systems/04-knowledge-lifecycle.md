# Knowledge lifecycle — freshness & invalidation

**Theme:** Operational knowledge ages—assume decay unless intentionally versioned.

Illustrative pivot:

Yesterday “Redis caching layer simplistic key-value” evolves toward **streams / consumer groups** choreography—documents treating only cache TTL semantics now **risk stale behavioural guidance**.

### Governance axes rehearse systematically

**Freshness clocks** anchoring factual statements (“true as-of commit SHA / doc rev”)  

Deliberate **invalidation triggers**—schema migrations, infra module upgrades, PSP API version jumps  

Knowledge **ownership lanes** tying updates to accountable roles—not orphan wiki drift  

Structured **semantic versioning analogue**—annotate internal ADRs/SPECs churn or epoch tags when radical shifts accumulate

Mandatory lab output: articulate **minimum three staleness hazards** hypothetical or historical—classification covers mis-applied optimisation, dangerously outdated security posture, invalidated operational runbook commands.

Discuss **silent summarization harm**: succinct memories erasing deprecation nuance—you still need branching historical narrative when parallel upgrade windows exist across tenants.

Integrate overlap with Sandbox security: invalidated advice must not resurrect secrets inadvertently when recycled.

### Checklist

- [ ] Breaking external dependency updates schedule explicit **retroactive SPEC review backlog** linkage.  
