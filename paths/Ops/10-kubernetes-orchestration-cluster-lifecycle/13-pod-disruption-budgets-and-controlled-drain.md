# Unit 13 — PodDisruptionBudgets and considerate drains

PDBs translate human availability commitments into scheduler-aware constraints guarding voluntary disruptions (node drains, rollout surges). They do not exempt you from buggy applications—yet they curb thundering herd surprises during upgrades responsibly.

Laboratory story: declare a conservative `maxUnavailable` for a StatefulSet or Deployment handling sessions; combine with `kubectl drain` respecting PDB denials ethically on disposable clusters only conscientiously ethically.

When PDB blocks maintenance, practise communication pattern: quantify risk trade-off, temporary relaxations with peer review—not silent deletion of guarding objects irresponsibly thoughtlessly ethically.
