# Unit 4 — CPU profiling harness (`net/http/pprof` + CLI workflow)

Practice enabling:

```go
import _ "net/http/pprof"
```

(or bench-only programmatic `pprof.StartCPUProfile` capturing)

Generate artefacts:

```
go tool pprof -http=:6060 cpu.prof      // or textual top / list commands
```

## Exercise

Fabricate knowingly slow algorithm (naive substring scanning, quadratic loops) verifying dominant functions appear unmistakably in **CPU profile**.

## Deliverable narration

Produce short **pseudo flame-graph interpretation paragraph** bridging textual `top`, `list`, optionally interactive graph.

Interview drill: summarise reading CPU graphs contrast heap profiles upcoming unit differentiate.

