# CPU profiling

**Theme:** Locate **truthful hotspots** via `pprof` CPU profiles—profiles beat intuition when JSON parsing, cryptography, regexp, or naive loops disguise themselves.

### Flow discipline

SYMPTOM (elevated latency / CPU saturation)  

MEASURE (RPS reproducible envelope)  

PROFILE (`go test -bench . -cpuprofile=cpu.out` or `curl` against a guarded `/debug/pprof/profile` endpoint in realistic non-prod settings).

Optimize targeted functions.  

VERIFY with profile delta + benchmarks.

Discuss **aggregation views**: flat vs cum, line-level vs function—pick the lens that matches the hypothesis (“who owns cycles on the critical path?”).

### LAB vectors

**JSON serialization** pressure—profile marshal/unmarshal hotspots; scrutinise generics / reflection artefacts if present.  

**Retry ownership spiral** caution—profiler reveals thundering herds or busy loops masquerading as “just retry”.

### Checklist

- [ ] Profiler capture window long enough versus timer resolution noise— annotate collection conditions.  
