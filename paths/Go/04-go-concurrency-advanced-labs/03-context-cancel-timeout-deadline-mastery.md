# Unit 3 — Context mastery layering: Cancel / Timeout / Deadline interplay

Operational trio internalisation:

```
context.WithCancel
context.WithTimeout
context.WithDeadline
```

Fabricate illustrative chain approximating mythical:

```
incoming HTTP-ish handler context (simulate)
   → simulated DB repository operation inheriting shrunk budget
   → nested gRPC-esque fake client call inheriting tightened cap again
```

No full frameworks obligatory—minimal structural fakes suffice if they honour `Done` propagation truthfully.

## Lab essay topics

Enumerate misconfigurations collapsing budgets unintentionally—notably spawning fresh `Background()` severing ancestry accidentally.

Articulate sentinel error readability mapping `context.DeadlineExceeded` handling vs generic error stringContains hacks historically frowned upon.

Interview expectation: verbally diagram tree cancellation waves like ripples succinctly—not elaborate animation—just coherence.
