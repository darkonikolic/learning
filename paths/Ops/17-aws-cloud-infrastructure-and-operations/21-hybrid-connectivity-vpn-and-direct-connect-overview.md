# Unit 21 — Hybrid connectivity: Site-to-Site VPN & Direct Connect concepts

Many enterprises attach AWS to on-prem Active Directory realms or legacy mainframes via **Site-to-Site VPN** tunnels or leased-line style **Direct Connect**. You may never provision DX in a learner account, yet architecture reviews demand vocabulary: BGP prefixes, failover tunnels, resilience expectations.

Laboratory alternative: emulate VPN concepts with overlapping route scenarios in diagrams, then correlate to Kubernetes clusters needing outbound access to corp HTTP proxies responsibly.

Troubleshooting pattern: asymmetric routing after corporate firewall updates—coordinate with netops using traceroute artefacts from earlier Linux (`02-*`) and container networking drills (`07-*`).
