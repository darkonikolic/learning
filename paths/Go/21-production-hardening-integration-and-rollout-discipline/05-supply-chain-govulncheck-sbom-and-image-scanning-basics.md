# Unit 5 — Supply Chain: govulncheck, SBOM, and Image Scanning

## Concept

Supply chain security means knowing what is in your binary and whether any of it has known vulnerabilities. `govulncheck` scans your Go module graph against the Go vulnerability database and reports only vulnerabilities reachable from your code — not just present in your dependencies. An SBOM (Software Bill of Materials) documents every package in your binary. `trivy` or `grype` scans your Docker image for CVEs in OS packages and language dependencies. These three tools answer: what am I shipping, and is any of it known-broken?

## Code

```bash
# 1. Check Go dependencies for known vulnerabilities.
#    Only reports vulnerabilities your code actually calls.
govulncheck ./...

# 2. Generate an SBOM in SPDX format from your Go binary.
#    Documents every module in the binary.
go version -m ./server > sbom.txt          # simple: module list from binary
syft ./server -o spdx-json > sbom.json     # full SBOM with syft

# 3. Scan your Docker image for CVEs.
trivy image myregistry/api-server:latest

# 4. Scan with grype (alternative to trivy)
grype myregistry/api-server:latest

# Output from trivy looks like:
# CRITICAL: 0  HIGH: 2  MEDIUM: 5  LOW: 12
# For each HIGH/CRITICAL: package name, CVE ID, fixed version.

# 5. Makefile CI target — add to your existing CI step.
# Makefile
.PHONY: ci
ci: test lint govulncheck image-scan

govulncheck:
	govulncheck ./...

image-scan: docker-build
	trivy image --exit-code 1 --severity HIGH,CRITICAL myregistry/api-server:latest
	# --exit-code 1 makes trivy return non-zero on findings → CI fails
```

## Exercise

**Build:** Run the three tools against your API service and its Docker image.
**Input:** Your service's Go modules and a built Docker image.
**Output:** Clean reports from `govulncheck`, and a `trivy` report showing zero HIGH or CRITICAL findings.
**Acceptance:** (1) `govulncheck ./...` exits 0 with no vulnerabilities. If it finds any, upgrade the affected module. (2) `trivy image <your-image>` — fix any HIGH or CRITICAL CVEs by either upgrading the Alpine base image tag or the affected Go dependency. (3) Add `govulncheck ./...` as a step in your `Makefile`'s `ci` target and confirm it runs in CI.

## Interview

- What is the difference between a vulnerability being present in a dependency vs being reachable in your code?
- Why does `trivy` find CVEs even in a `scratch`-based image?
- An SBOM is useful after an incident. Explain how.
