# Docker + container failure

**Theme:** Container **presence ≠ health**. Probe lifecycle, cgroup limits, mounts, egress.

### Drill catalogue

Memory pressure  

OOM / cgroup kills vs app-level exhaustion  

Crash restart loops attributable to bootstrap mis-ordering  

Anonymous vs named **volume drift** parity  

Bridged vs overlay **network partitioning** artefacts mis-tagged as application bugs  

### Incident loop echoes

Mandatory triple for each tabletop:

1. Hypothesis granularity at kernel / daemon / app layering  

2. Validation via reproducible diminished cluster or recorded failure bundle  

3. Rollback doorway (pinned image digest? config revert choreography?)

### Checklist

- [ ] Dockerfile / entrypoint sequencing reviewed when exit code ambiguity surfaces.  
