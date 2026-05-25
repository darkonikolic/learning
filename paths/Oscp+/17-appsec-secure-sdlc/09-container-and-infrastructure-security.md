# Container and Infrastructure Security

Secure containers start at the Dockerfile. Kubernetes security is RBAC + network policies + runtime monitoring.

## Resources

- Docker Bench for Security: https://github.com/docker/docker-bench-security
- kube-bench: https://github.com/aquasecurity/kube-bench
- kube-hunter: https://github.com/aquasecurity/kube-hunter
- Falco: https://falco.org/
- TryHackMe "Kubernetes for Everyone": https://tryhackme.com/room/kubernetesforyouly

## Secure Dockerfile Patterns

```dockerfile
# BAD — root user, fat base image, secrets in layer
FROM ubuntu:latest
RUN apt-get install -y curl python3
ENV DB_PASSWORD=supersecret
COPY . /app

# GOOD — non-root, minimal image, multi-stage, no secrets
FROM golang:1.21-alpine AS builder
WORKDIR /build
COPY . .
RUN go build -o app ./cmd/server

FROM alpine:3.19
RUN adduser -D -u 10001 appuser
COPY --from=builder /build/app /usr/local/bin/app
USER appuser
EXPOSE 8080
ENTRYPOINT ["app"]
```

```dockerfile
# Key rules:
# - USER appuser (never root in production)
# - Minimal base: alpine, distroless, scratch
# - Multi-stage builds (no build tools in final image)
# - No ENV with secrets — inject at runtime
# - Pin base image versions (not :latest)
# - .dockerignore to exclude .git, .env, secrets
```

## Trivy Container Scan

```bash
# Scan public image
trivy image nginx:latest

# Scan with severity filter
trivy image --severity HIGH,CRITICAL myapp:latest

# Fail CI on critical
trivy image --exit-code 1 --severity CRITICAL myapp:latest

# Scan local tar
docker save myapp:latest | trivy image --input -

# Scan IaC (Terraform, Kubernetes YAML)
trivy config ./k8s/
trivy config ./terraform/
```

## Docker Bench for Security

```bash
# Run CIS Docker Benchmark checks
docker run --rm --net host --pid host --userns host --cap-add audit_control \
  -e DOCKER_CONTENT_TRUST=$DOCKER_CONTENT_TRUST \
  -v /etc:/etc:ro \
  -v /usr/bin/containerd:/usr/bin/containerd:ro \
  -v /usr/bin/runc:/usr/bin/runc:ro \
  -v /usr/lib/systemd:/usr/lib/systemd:ro \
  -v /var/lib:/var/lib:ro \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  --label docker_bench_security \
  docker/docker-bench-security
```

## Kubernetes Security

```bash
# Check what current service account can do
kubectl auth can-i --list
kubectl auth can-i --list --namespace=kube-system

# View all RBAC roles
kubectl get clusterroles
kubectl get roles --all-namespaces

# Check for overly permissive bindings
kubectl get clusterrolebindings -o json | jq '.items[] | select(.roleRef.name=="cluster-admin")'

# View network policies
kubectl get networkpolicies --all-namespaces

# Check pod security settings
kubectl get pods --all-namespaces -o json | jq '.items[] | select(.spec.securityContext.runAsRoot==true)'
```

## kube-bench (CIS Kubernetes Benchmark)

```bash
# Run in cluster
kubectl apply -f https://raw.githubusercontent.com/aquasecurity/kube-bench/main/job.yaml
kubectl logs job/kube-bench

# Run locally against cluster
kube-bench run --targets master
kube-bench run --targets node
```

## kube-hunter (Active Kubernetes Pentesting)

```bash
# Run from inside cluster (check internal exposure)
docker run -it aquasec/kube-hunter --pod

# Run from outside cluster (check external exposure)
kube-hunter --remote <cluster-IP>

# Passive mode only
kube-hunter --remote <cluster-IP> --passive
```

## Falco (Runtime Security Monitoring)

```bash
# Install via Helm
helm repo add falcosecurity https://falcosecurity.github.io/charts
helm install falco falcosecurity/falco --set tty=true

# Example Falco rule — detect shell in container
# - rule: Terminal shell in container
#   desc: A shell was used as the entrypoint/exec point into a container
#   condition: container.id != host and proc.name = bash
#   output: Shell in container (user=%user.name container=%container.name)
#   priority: WARNING

# View Falco alerts
kubectl logs -l app=falco -n falco
```

## Ethical Note

kube-hunter active mode sends real attack probes. Only run against clusters you own or have explicit authorization to test.
