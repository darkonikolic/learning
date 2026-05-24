# Optimization thinking

**Theme:** “Working” is floor—**optimise** against measured waste: time, tokens, coordination overhead, cognitive load.

### Dimensions to rehearse

**Claude workflow**

Drive **iteration count** down with better Rules/Skills/retrieval—example target class: 20 → 10 **when** quality holds or improves.

Compress **prompt / context tokens** without losing invariants—e.g. 2000 → 700 **when** chunking and pointers suffice.

**Agent orchestration**

Reduce **handoff count** when state contracts stabilise—e.g. 5 → 3 **without** skipping QA or approval.

**Application layers**

Symfony / Laravel: trim **accidental complexity** in service graphs.  

Go: profiling-led hotspots (tie to your performance syllabus).  

Vue/JS: bundle and interaction cost where relevant.

### LAB rule

Per system under study, list **three optimisations** with:

**Before metric** snapshot  

Hypothesis  

**After** verification  

Rollback if regression

Discuss **Pareto** focus—improve movers of SLO, cost, or team velocity—not vanity micro-optimisations.

### Checklist

- [ ] Optimisations cite **verification** artefacts—benchmark, trace, reviewer sign-off—not only intuition.  
