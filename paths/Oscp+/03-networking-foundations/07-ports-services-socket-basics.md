# Unit 07 — Ports, services, fingerprints

## Theme

Associate common listening ports with service intent and tooling.

## TryHackMe

Complete **Network Fundamentals** milestone tasks not yet crossed off unless already satisfied honestly.

## Ubuntu drills

```bash
sudo ss -tulpn | head -40
sudo nmap -sV localhost
```

(Optional narrow scan.) Do **not** scan third-party hosts without explicit permission.

## Memorization targets (purpose, not trivia)

Associate services you will collide with routinely:

22 SSH • 53 DNS • 80 HTTP • 443 HTTPS • **445 SMB** • **389 LDAP** • **88 Kerberos** • **3389 RDP**

Understand these as **patterns** attackers enumerate—not flashcards devoid of semantics.

## `netcat`/SSH micro drills

Demonstrate purposeful local loopback chatter or SSH banner grab on your VMs only.

## Learning outcome

When `ss` shows `LISTEN` on surprising port → you classify benign vs suspicious next-step triage thoughtfully.
