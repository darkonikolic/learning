# Unit 5 — Supply chain: `govulncheck`, SBOM discipline, and container image scrutiny

Companion to **fundamentals dependency honesty** (`go.mod` sums)—this turns “integrity on disk” into **continuous vulnerability posture**.

## Goals

- Run **`govulncheck`** (or successor official vulnerability tooling) interpreting **called vs reachable** nuances—know why “CVE present in module graph” ≠ “exploitable in your binary”.
- Produce a **minimal SBOM** artefact during CI for one service (Syft/other standard generator acceptable) and state what you’d **actually** operationalise downstream (scanner feeds, approvals, SLA).
- Integrate **image scanning** basics ( distroless vs debian slim trade-offs mirrored at policy level—not vendor tutorial) aligning base image pinning with rebuild cadence.

## Concepts to internalise

- **Dependency audits** ↔ **running-artefact audits**: different scanners, different freshness contracts; reconcile both mentally before release gates.
- **Retracted modules** correlation with upgrade policy—tie back to semver/replace cautions earlier in the curriculum.

## Practice sketch

Pick the **same** repo you hardened in Units 01–03. Extend CI conceptually (`bash` sketches acceptable):

```
module vulnerability scan producing non-zero informational output analysed
artifact SBOM archived with semver tag association narrative
Dockerfile rationale note: smallest change improving scanner noise vs debuggability
```

## Interview prompts

- How do you prioritise patching when **severity is high but reachability uncertain** mid-sprint?
- Where does **checksum verification** (`go.sum`, image digests) end and **trust anchor** debates begin?

## Acceptance criteria

Short **risk register** listing five rows: vuln tooling false negative class, SBOM staleness hazard, suppressed CVE governance risk, pinning versus drift, emergency rebuild communication path.
