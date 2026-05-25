# Unit 19 — Resilience, backup, and DR patterns (RDS, S3, snapshots)

Translate `20-*` reliability ideas into AWS primitives: automated **RDS snapshots** with tested restores, **S3 versioning** + lifecycle rules, **cross-region replication** only when RPO demands justify cost. Always script a restore rehearsal summary—even if the rehearsal happens quarterly in a real job.

Document RPO/RTO targets qualitatively for a demo ecommerce database: how many minutes of data loss are tolerable, which snapshot window satisfies that, and who approves emergency PITR spends.

Pair with Terraform (`10-*`) cautiously: removing `DeletionProtection` via IaC is a production foot-gun—use policy checks introduced in `10-*` trailing units.
