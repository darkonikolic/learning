# Filesystem + network restriction

**Theme:** **Least privilege by default.** Full disk + unrestricted egress are convenient until they are catastrophic.

### Filesystem stance

Prefer **workspace-only** read-write; system paths read-only at most; block traversal into **unrelated directories** (other projects, `$HOME`, backup volumes) unless there is written justification and review.

Classify helpers into **read / write / execute** lanes—generation tasks need write **only** on generated artefacts paths.

### Network stance

| Posture | When |
|---------|------|
| **Denied by default** | Untrusted prompts, broad agent autonomy |
| **Allow-list** | Package mirrors, documented API docs, mocked dependency hosts |
| **Supervised egress** | Real cloud APIs behind explicit approval gates |

Labs: deliberately **break** overly broad permissions inside a disposable environment—observe how fast damage scales—then **tighten** policy and capture the sandbox template deltas.

### Checklist

- [ ] DNS egress side channels (analytics, telemetry) considered part of blast radius—not only “evil curl.”  
