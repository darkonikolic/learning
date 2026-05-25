# Unit 20 — Cost awareness, tagging, and service quotas

Professional AWS work includes **cost allocation tags**, **budgets + anomaly detection**, and understanding **service quotas** before large-scale load tests take down an API Gateway unexpectedly. This is not FinOps certification depth—just enough to partner credibly with finance peers.

Exercise: define a mandatory tag schema (`Environment`, `Owner`, `CostCenter`) you would enforce via SCP or IaC validators. Describe how Grafana/Prometheus billing exporters differ from AWS Cost Explorer (both useful, different fidelity).

When scaling EKS (`10-eks*` narratives), remind yourself control plane hourly charges plus NAT Gateway data processing often dominate guesses—surfacing early in architectures avoids shock.
