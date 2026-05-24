# Docker sandbox

**Theme:** Make the default execution story **container-first** for AI-assisted dev: image + mounts + network policy you control.

### Core objects

**Image** — reproducible filesystem baseline.  

**Container** — running instance with cgroup + network namespace (still not magic—kernel shared).  

**Volume** — named or bind data—**bind mounts are the usual foot-gun**.  

**Network** — bridge / none / custom—default “everything egress” is dangerous for unattended agents.

### Mount discipline

**Anti-patterns:** `-v /:/host` or mounting entire `$HOME` into an agent-driven container.  

**Better:** mount **only** the project workspace (e.g. `claude-workspace/` or repo root you designate).  

Use **read-only** where possible: `:ro` for dependencies you should not mutate; `:rw` only where builds must write.

### Practice layout

Create a dedicated tree (example name) **`claude-workspace/`** (or your repo root with strict mount policy) and configure tooling so assistants **only** operate there in automated flows.

**Symfony / Go:** run builds, tests, and codegen inside the container; host holds editor only if you want separation.

### LAB

Prove **no accidental host visibility**: from inside the execution environment, paths outside the workspace must be absent or empty by design—not “hidden by convention.” Document what still leaks (Docker socket mounts, forwarded SSH agent)—and treat those as conscious trust breaks.

### Checklist

- [ ] Dockerfile or compose documents **why** each mount exists—orphan binds removed.  
