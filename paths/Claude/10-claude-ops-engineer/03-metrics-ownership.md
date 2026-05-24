# Metrics ownership

**Theme:** Emotional temperature untrusted — **instruments** adjudicate rivalry among hypotheses.

### Core families (iterate combinations)

Latency percentiles  

CPU saturation / throttle signals  

RSS / cgroup pressure artefacts  

Broker / internal **queue depth**  

Error-ratio vs success throughput skew  

Saturation interplay (DB connections, fd exhaustion)

### Separation practice

Articulate deliberately:

| Class | Means |
|-------|-------|
| **Signal** | Expected to move sharply if hypothesis holds; ties to causal model. |
| **Noise / weak prior** | Fluctuates without discriminating culprit class without extra stratification. |

### Practice vignettes

| Layer | Incident seed |
|-------|----------------|
| **Go worker** | Perceived sluggishness—is batching starvation or IO wait dominant in metrics corroboration? |
| **DB** | Elevated latency—CPU vs locking vs buffer pool anomalies disambiguated historically. |
| **K8s** | **CrashLoop / eviction** hinted via restart counters + resource timelines before pod delete theater. |

### Checklist

- [ ] dashboards / PromQL equivalents sketched—even if hypothetical training cluster.  
