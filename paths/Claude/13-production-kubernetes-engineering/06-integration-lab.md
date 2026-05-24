# Integration lab — production Kubernetes ownership

Composite scenario forcing cross-theme reasoning — not isolated YAML trophies.

Potential incident bouquet interleaving ingress mis-route, unintended NetworkPolicy starvation, Scheduling Pending puzzle from taint churn, PDB blocking upgrade midway, autoscaler amplification exposing CPU request lies.

Compose operational narrative artefacts:

Traffic path enumerated end-to-end (DNS → LB → Ingress → Service → Pods) annotated with failure hypotheses.

Isolation matrix snapshot (acceptable edges only).

Scheduling state truth table (affinities respected?).

Elasticity recap (desired vs realised scale events & constraints).

Recover rehearsal ordering (traffic drain → config revert → phased roll forward verifying signals).

Checkpoint reflection: articulate where prior instinct would have blindly redeployed vs evidence-led convergence.
