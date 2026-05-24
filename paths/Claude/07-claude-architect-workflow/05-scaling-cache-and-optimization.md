# Scaling, cache strategy, and optimization ownership

**Theme:** Beyond “runs” — interrogate load shape, caching truth, duplicated work, MySQL hotspots, queue backpressure — under **architecture-level tradeoffs**.

### Scaling dimensions (discussion prompts with Claude)

| Dimension | Probe |
|-----------|-------|
| **Horizontal** | stateless tiers, partitioning, shard awareness |
| **Vertical** | single-node ceilings you still consciously accept temporarily |
| **Data / MySQL** | readReplicas, hotspots, paging, index choreography |
| **Queue / worker** | consumer parallelism vs ordering / poison exposure |
| **Distributed truth** | timeout budgets, cascading failure containment |

### Cache strategy checklist

Declare explicitly per endpoint / read model:

| Decision | Answer |
|----------|--------|
| **What is cached** | keys, payloads, TTL posture |
| **Invalidation triggers** | event-driven vs time-based sweep |
| **Consistency class** | read-your-writes guarantees or eventual-only |
| **Stampede mitigation** | single-flight patterns, probabilistic TTL jitter |

Stale cache classes are architectural failures — classify them explicitly when debugging.

### Optimization lab rule

Minimum **three** optimisation candidates per meaningful delivery slice labelled across:

1. Complexity / readability  
2. Cost / infra  
3. Latency / throughput envelope  

Defer only with rationale tied to Goal / SUCCESS frozen upstream.

### Checklist

- [ ] Scaling claims cite **measurable** hypotheses or monitoring hooks you will attach.  
