# RED • USE • golden signals in practice

**Theme:** Pick **one primary model per component class** so on-call brains do not context-switch models every page.

| Component class | Favoured lens | Example signals |
|-----------------|---------------|-----------------|
| HTTP / gRPC API | RED (+ saturation of thread pool) | RPS, 5xx ratio, latency histogram |
| Worker / queue consumer | Rate, age of oldest message, process time | lag, poison rate, retry storms |
| DB primary | USE + query latency | connections, lock waits, disk saturation |
| Cache | USE + hit ratio | eviction pressure, latency |

LAB: Sketch **one dashboard row per service tier** tying RED/USE to your SLO numerator/denominator story.
