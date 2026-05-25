# Unit 15 — AWS Organizations, SCPs, and cross-account access patterns

Large AWS estates centralise guardrails through AWS Organizations and **Service Control Policies** (SCPs) constraining what member accounts can ever enable—even if an IAM policy inside the account looks permissive on paper. This is not `19-*` day-one material, but you must recognise the existence of control planes above single-account IAM when designing landing zones.

Pair SCP thinking with **cross-account IAM roles** (typically `sts:AssumeRole` from a shared tooling account) so CI/CD or human break-glass never stores long-lived access keys on laptops. Sketch a three-account mental model: `security`, `workloads`, `network`—even if your lab only simulates one account.

Verification habit: when a pipeline suddenly cannot create an S3 bucket, consider **implicit deny via SCP** before spending hours debugging IAM inline policies in isolation.
