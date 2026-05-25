# Unit 18 — Edge delivery: CloudFront, WAF, and ACM in practice

Public HTTP surfaces often terminate TLS at **CloudFront** or **Application Load Balancers** with certificates from **ACM**. Professional operators understand cache key behaviours, origin shielding, and when to enable **AWS WAF** managed rule groups versus custom rules—without enabling every rule aggressively blocking legitimate API clients.

Lab substitute if budget-constrained: keep using `12-*` Traefik/Nginx locally but map each feature (TLS cert auto-renewal, geo headers, request logging) to its AWS analogue in writing.

Incident tie-in: when users see sporadic 403s, differentiate WAF vs security group vs origin misconfiguration using edge access logs (conceptual workflow).
