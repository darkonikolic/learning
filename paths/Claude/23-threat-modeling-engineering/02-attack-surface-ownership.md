# Attack surface ownership

**Theme:** Name **everything an adversary—or buggy client—can reach** across environments: URLs, sockets, queues, admin panels, MCP tools, terraform state backends, artefact stores.

Ownership question: **who maintains the catalogue** when new ports, webhooks, or debug routes appear overnight?

### Surfaces typical in your stack drills

Symfony HTTP routes + internal CLI + dev probes  

Go binaries / health endpoints / metrics ports  

**JWT** validation paths (issuer, audience, clock skew, key rotation story)  

**OAuth** redirect chains, token storage, refresh misuse classes  

Message **queues** ingress (producer trust, enqueue authZ)  

CI/CD artefacts & preview environments widening exposure quietly

Exercise: sketch **boundary inventory table** listing entrypoint, authenticated?, data class touched, owning team—then mark **internet reachable vs private only**.

Discuss **risk ownership**: ambiguous surfaces linger when “everyone owns it” paradoxically translates to nobody.

Widening the attack surface often **accelerates privilege escalation (EoP)**: debug routes without auth layering, MCP filesystem mounts that are too broad, or service accounts granted excessive IAM scopes.

Mandatory lab heuristic: annotate **trust assumptions per row**—“we assume callers already X”—then challenge whether invariant holds under breach of adjacent component.

Discuss **verification**: stale inventory worse than none—schedule diff review when infrastructure modules merge.

### Checklist

- [ ] Each new external integration receives **documented entrypoint + data sensitivity** before merge—not after incident.  
