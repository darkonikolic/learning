# A/B workflow thinking

**Theme:** Principals compare **alternatives deliberately** instead of rewriting whimsically—especially across **frontend / backend / worker / Terraform / shared lib** seams.

### Method discipline

Define **A** and **B** precisely (same workload slice, comparable time windows when possible).

Pre-register **metrics**: quality rubric subset, tokens, iterations, latency, infra signal.

Avoid peeking prematurely—honest notebooks beat self-deception.

### Illustrative arenas

**Claude / retrieval**

A: Large monolithic context dump  

B: **Partitioned retrieval** chunks with explicit ownership tags  

Measure: answer quality scorecard, token load, repair iterations.

**Go workers**

A: Pool size / concurrency setting 10  

B: Setting 25  

Measure: p95 job latency, queue depth, CPU saturation—reject “felt faster.”

**Symfony / cache boundaries**

A: Cache boundary strategy X around aggregate reads  

B: Strategy Y  

Measure: hit ratio value **and** correctness / stale risk narrative.

### Large-repo note

In **monorepos**, keep A/B scope **narrow**—one package or service graph neighborhood—to attribute effects. In **polyrepos**, version alignment between experiments must be explicit or results lie.

### LAB

Per system class you touch, document at least one **A vs B** comparison with **decision** citing Experiment Template.

### Checklist

- [ ] A/B pairs avoid **simultaneous confounds** (two unrelated changes in one “experiment”).  
