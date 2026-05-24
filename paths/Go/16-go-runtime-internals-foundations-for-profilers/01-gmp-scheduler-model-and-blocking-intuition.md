# Unit 1 — Scheduler model (G–M–P) for purposeful performance reasoning

Interpret **G** goroutine descriptors, **M** OS-thread workers, **P** logical processors/context carrying runnable queues—high level enough for interview storytelling without pretending you’ll hand-derive preempt points daily.

Linkage to earlier work:

Why “more goroutines” thrashes CPU-heavy tasks (Area `15` Unit 9) maps to runnable scheduling contention & `P` starvation intuition.

Practice: summarise **blocking syscalls**, **park/unpark**, and **work stealing** verbally from current reputable runtime docs—not legacy blog myths blindly.
