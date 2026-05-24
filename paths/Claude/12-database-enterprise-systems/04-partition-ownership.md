# Partition ownership

**Theme:** Scaling write / index heat via **logical sharding schemes** introduces cross-partition nightmares—design ownership anticipates hotspots and rebalancing nightmares early.

Decision angles:

Partition **key cardinality** realism  

Uneven **skew** (super tenant / mega-customer tsunami)  

Cross-partition **transaction impedance** forcing saga-like compensations externally  

Historical **rebalancing** manoeuvres doubling write amplification temporarily

### LAB — heuristic strategy sketch

Twin heavy entities **orders vs payments**:

Evaluate co-locate vs segregate philosophies  

Discuss **compound keys**, time bucketing pitfalls, hashing vs modulus tradeoffs — and explicitly document **dual-read windows** while migrating rows without integrity tears.


Avoid presenting one universal answer—expose **evaluation matrix** tying business access patterns quantitatively—even if illustrative estimates only.

### Checklist

- [ ] Escaped generic “shard by user id always” tautology defended or debunked with workload specificity.  
