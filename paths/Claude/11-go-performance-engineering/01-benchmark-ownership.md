# Benchmark ownership — performance framing

## Phase framing — Go Performance Engineering (“Phase 6.2”)

**Units in this folder:** `01`–`05` (topic order only).

### Themes carried through

**pprof** • **CPU profiling** • **memory profiling** • vigilance against **goroutine leaks** • **escape analysis** • **benchmark discipline** • **GC pressure literacy**

### Working loop (prefer this ordering)

```
 SYMPTOM  →  MEASURE  →  PROFILE  →  OPTIMIZE  →  VERIFY
```

**Checkpoint mentality:** instincts shift from vague “slow code” complaints toward **instrumented optimisation** defended by before/after numbers.

### Go performance slice worksheet (reuse per drill)

| Field | Holds |
|-------|-------|
| **SYMPTOM** | Latency / allocations / saturation—where (which handler or worker stage). |
| **MEASURE** |Bench command, profiling flags, reproducible workload shape. |
| **PROFILE** |pprof modality (CPU, heap, goroutine block, mutex) + where time or bytes live. |
| **OPTIMIZE** |Minimal diff targeting proven hotspot—not speculative rewrite. |
| **VERIFY** |Bench delta + behavioural tests + regression leak watch (especially goroutine count). |

---

**Theme (this unit):** **Measure before folklore.** Ownership of benchmarking means stable inputs, deterministic builds (`-count`, warm-up policy honesty), guarding against optimised-away work.

### LAB — worker queue backbone

Bench the ** dequeue / process / ack** narrative under realistic payloads—compare baseline vs contended scenarios; record wall vs ns/op artefacts with variance awareness.

Expose anti-patterns: micro-benchmark happiness lying via dead-code elimination absent side effects (`Sink` tricks when appropriate).

### Checklist

- [ ] **`testing.B` parallelism** consciously chosen—not accidental shared-state fiction.  
