# Unit 4 — Leaks, deadlocks, blocked-channel forensic drills

Controlled destructive exercises—then heal:

| defect class | trigger sketch | remediation principle |
|--------------|----------------|-----------------------|
| **goroutine leak** | spawned worker ignoring parent `ctx.Done()` perpetually loops | unify lifecycle join |
| **channel block** mismatches | forgotten receiver / closed prematurely mis-synchronisation | unify state machine choreography |
| **deadlock** | inconsistent lock/channel acquisition ordering | deterministic acquisition policy / refactor pipeline |

Produce micro-postmortem bullet lists per class emphasising preventative heuristics teachable verbally under interview hypothetical debugging prompts.

Interview storytelling goal: interviewer describes symptom logs—you outline diagnostic narrowing steps without insisting single silver-bullet tool blindly.
