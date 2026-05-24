# Unit 17 — ECS/Fargate vs EKS: choosing a container platform on AWS

**Amazon ECS** (often with Fargate) packages task definitions, service discovery, and scaling with less moving parts than **EKS**, which brings the full Kubernetes operational surface you already practised in `08-*`/`09-*`. Neither is universally superior: choose based on team skills, desired extension points, and integration with existing GitOps stacks.

Exercise: document a decision matrix for a Symfony + Go API stack: who owns cluster upgrades, how Helm charts port, what observability agents you must run, and how CI promotes images. Even a one-page matrix is enough to prove structured thinking.

Cost lens: Fargate removes node management but can surprise at steady high CPU—pair with cost dashboards later (`20-*` reliability themes) before production promises.
