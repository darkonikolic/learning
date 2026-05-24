# State recovery and checkpoints

**Theme:** Agents and tools fail—**durable workflow** means you can **save**, **detect loss**, **resume** without moral panic.

### Failure modes to rehearse

QA blocks release—shared state must record **what failed** and **what remains valid**  

**Tool timeout** mid-handoff—partial writes need discard or idempotent replay rules  

**Context loss** (session reset, crashed runner)—reload from **CHECKPOINT**, not from memory

### Recovery macro-pattern

```
 CHECKPOINT written (shared state version bump)
        → agent or tool fails
                  → RECOVERY procedure selects last good checkpoint
                           → RESUME with explicit re-validation of STATE CONTRACT
                                     → CONTINUE from authorised hop
```

Checkpoints can be: git tag, SPEC revision note, ticket comment with artefact links, CI artefact id—**pick what your org can query later**.

**LAB:** deliberately break a handoff, a single agent step, or a tool call in a **throwaway** environment; practise **detect → recover → continue** and log what was lost vs restored.

### Checklist

- [ ] Recovery never **skips** approval gates that applied before the failure—re-open scope if needed.  
