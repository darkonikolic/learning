# Unit 16 — Transit Gateway style multi-VPC connectivity (conceptual lab)

When services outgrow a single VPC, teams connect spoke VPCs through **AWS Transit Gateway** (or peering patterns for smaller footprints) so shared services (egress inspection, centralised logging, private API endpoints) remain reachable without duplicating NAT infrastructure everywhere.

You may not build a full TGW lab on Free Tier; still draw address plans showing **non-overlapping RFC1918 CIDRs**, route table priorities, and where **inspection VPCs** live. Compare mental model to Kubernetes overlay networking (`07-*`, `08-*`).

Failure mode to rehearse narratively: asymmetric routing after adding a new spoke—document how you would prove with VPC Flow Logs (conceptual) rather than guessing security groups first.
