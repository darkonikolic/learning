# Load + chaos testing ownership

**Theme:** Produce mindset for **risk under reality’s thumb** — not “unit green” narcissism alone.

Stress scenarios (exemplary ladder — tailor numbers):

| Class | Spike |
|-------|-------|
| **Load** | 1 k → **5 k sustained-ish** coherent requests respecting auth reality |
| **Worker crash** | SIGKILL midway batch — queue drain & duplicate semantics survive |
| **Queue delay / backlog** | consumer slower than spike — SLA story breathes honestly |
| **Network latency jitter** | slow dependency responses — timeouts don’t deadlock platform |

Interpretation rule: regressions flagged here **block “done”** until owned or waived with explicit stakeholder debt note.

### Concept tags

**Load ownership**  

**Chaos ownership** (blast radius budgeting + revert story before you pull levers)

### Safety note

Exercise chaos in isolated sandboxes predictable to your org — destructive commands never surprise shared environments.

### Checklist

- [ ] Scenario matrix references **measurable SLO hypotheses** drafted earlier in SPEC lineage.  
- [ ] Tear-down restores baseline queues / topics / DB clones used.  
