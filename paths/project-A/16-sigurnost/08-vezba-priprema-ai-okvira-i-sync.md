# 08 — Vežba: priprema AI-okvira i sync (sigurnost)

Pripremaš AI-okvir za bezbednost klastera i pristupa, pa validiraš RBAC, network policy i image scan.

## Cilj

- okvir koji forsira least-privilege RBAC, network izolaciju i čiste image-e
- dokazano: nema preširokih dozvola, default-deny mreža, bez critical CVE

## Deo A — Priprema AI-okvira za sigurnost

### A1 — Mapiraj

| Potreba | Postoji? | Gde |
|---------|----------|-----|
| Security persona | da | `/security-trainer` |
| K8s/secrets checklist | delom | `k8s-manifest-checks`, `secrets-hygiene` |

### A2 — Odluka (anti-sprawl)

`/system-maintainer` + `process-feedback`: kandidat rule `cluster-security-checks` (RBAC bez `cluster-admin` za app, NetworkPolicy default-deny, no privileged pods). Uvedi — sigurnost je sistemska briga.

### A3 — Minimalni dodatak (primer)

```
# kandidat: cluster-security-checks
- ServiceAccount po servisu; bez cluster-admin bindinga za aplikacije.
- Default-deny NetworkPolicy, pa eksplicitni allow.
- Bez privileged/hostNetwork; runAsNonRoot, readOnlyRootFilesystem gde može.
```

## Deo B — Praktičan rad (sync)

### Validacija sigurnosti

```bash
kubectl auth can-i --list --as=system:serviceaccount:app:web
docker run --rm aquasec/trivy image <slika>:<tag>   # bez HIGH/CRITICAL
# kube-bench za CIS benchmark na klasteru
```

## Validacija — acceptance kriterijumi

- [ ] odluka A2 doneta preko `/system-maintainer`
- [ ] `can-i --list` pokazuje least-privilege (nema `*`)
- [ ] `trivy` bez HIGH/CRITICAL (ili svesno prihvaćeno sa razlogom)
- [ ] default-deny NetworkPolicy aktivna
- [ ] sync zapisan u `decision_log.md`

## AI workflow

```
Daj least-privilege RBAC (Role + RoleBinding) za servis kome treba samo
read na ConfigMap-e u svom namespace-u, i default-deny NetworkPolicy. Objasni.
```
