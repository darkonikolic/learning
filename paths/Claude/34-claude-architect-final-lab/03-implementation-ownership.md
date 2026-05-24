# Implementation ownership

**Unit:** `03` of final lab (week 3 focus).

**Theme:** Implementation stays tied to the **frozen SPEC** — detect and repair **drift** instead of normalising it.

### Loop

```
 implement a small vertical slice
       → verify (tests + checks against acceptance)
             → diff SPEC vs behaviour
                   → repair code or update SPEC with version + reason
                         → repeat until green
```

### Practice

Symfony **CQRS** slice: command → handler → aggregates/projections aligned to acceptance ids.  

Go **worker**: consumer matches retry, DLQ, and idempotency from the spec.  

**MySQL**: schema/migration steps match the data model in the spec.

### Test engineering ownership (implement the verification pyramid)

Minimal bar for Week 3—evidence artefacts, not “we have tests somehow”:

- **Unit**: fast domain/unit suite on payment aggregate/rules; table-driven tricky cases  

- **Integration**: HTTP/command path hitting real MySQL (+ migration), queue client fakes or brokers in CI profile  

- **Contract**: PSP façade / internal event schema guarded (consumer-driven or schema registry discipline your stack allows)  

- **Property**: at least **one** property or heavy generator case on invariant you fear (replay, totals)  

- **Load smoke**: scripted k6/ghz/hey against staging profile—captures baseline + tail before you optimise in Week 7  

- **Chaos**: tame failure (docker pause on broker shard, iptables latency) with **explicit expected steady signals** queued for Week 6 observability rehearsal  

Pointers: **`09-enterprise-depth-appendix.md` § Test engineering.**

### Database enterprise slice (implement with eyes open)

Ownership means you can articulate how your MySQL lanes behave under concurrency:

**Isolation levels** in use (`READ COMMITTED` vs `REPEATABLE READ` tradeoffs)—phantom/read skew stories you accepted  

**Deadlock anatomy** practice: show one EXPLAIN deadlock log / graph reading exercise on contended refund path  

**Replication lag** implication: eventual reads vs command path authority  

**Partitioning hints** later (sharding postponed is fine—capture hot key risk)  

**Optimistic concurrency** (`version`/etag row) vs **pessimistic** (`FOR UPDATE`) on inventory reservation—with explicit deadlock/livelock avoidance posture  

Canonical notes: **`09-enterprise-depth-appendix.md` § Database enterprise.**

### Adversarial LAB

Introduce a deliberate **spec ambiguity** or silent change in one place — the workflow must **detect drift**, propose **repair**, and update artefacts (not chat-only fixes).

### Checklist

- [ ] Verification is owned: author is not always the sole sign-off persona for high-risk slices.  

- [ ] CI (or repeatable script path) executes **integration** suite touching MySQL—not only mocked units.  

- [ ] At least one concurrency-sensitive path explains **chosen isolation + locking** strategy in short prose.  
