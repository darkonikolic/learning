# Unit 11 — Image hardening: non-root, capabilities, read-only roots

As images move toward production-facing clusters, predictable UID/GID, dropped Linux capabilities, and read-only container roots materially reduce escalation blast radius—even before admission controllers enforce profiles.

In labs, rebuild a Symfony or Go image so the main process UID is not `0`, mount writable paths explicitly for cache dirs, and iterate `docker inspect` verifying effective user. Pair with Compose override volume permissions consciously rather than widening host permissions lazily.

Document trade-offs: installers expecting root, PHP-FPM user mapping, ephemeral `/tmp`. Capture one rollback story when hardening silently breaks health checks—that narrative is interview-grade depth.
