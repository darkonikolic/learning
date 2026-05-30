# 09 — Vežba: priprema AI-okvira i sync (load balancer)

Pripremaš AI-okvir za ALB/ingress i TLS, pa verifikuješ rutiranje, health check-ove i sertifikat.

## Cilj

- okvir koji pokriva LB rutiranje, health check-ove i TLS higijenu
- dokazano: saobraćaj prolazi kroz LB, health check-ovi rade, TLS validan

## Deo A — Priprema AI-okvira za load balancer

### A1 — Mapiraj

| Potreba | Postoji? | Gde |
|---------|----------|-----|
| DevOps persona | da | `/devops-engineer` |
| Ingress/TLS checklist | delom | `k8s-manifest-checks` |

### A2 — Odluka (anti-sprawl)

`/system-maintainer` + `process-feedback`: proširi `k8s-manifest-checks`/`terraform-checks` stavkama za LB (health check path, HTTPS redirect, TLS verzija/cipher, deregistration delay). Bez novog rule-a ako pokrivaju.

### A3 — Minimalni dodatak (primer)

```
# dopuna checks (load balancer)
- Health check cilja /health, ne /; pragovi razumni (ne flapping).
- HTTP → HTTPS redirect; TLS >= 1.2; bez slabih cipher-a.
- Deregistration delay da se in-flight zahtevi završe pri deploy-u.
```

## Deo B — Praktičan rad (sync)

### Verifikacija LB-a i TLS-a

```bash
curl -fsS https://<host>/health
aws elbv2 describe-target-health --target-group-arn <arn>   # svi healthy
docker run --rm drwetter/testssl.sh https://<host>          # TLS ocena
```

## Validacija — acceptance kriterijumi

- [ ] odluka A2 doneta preko `/system-maintainer`
- [ ] saobraćaj prolazi kroz LB do servisa
- [ ] svi target-i `healthy`
- [ ] HTTPS radi, TLS >= 1.2, redirect sa HTTP-a
- [ ] sync zapisan u `decision_log.md`

## AI workflow

```
Hoću ALB ispred [servisa] sa HTTPS, redirect-om sa HTTP i health check-om na /health.
Daj konfiguraciju (Terraform/ingress) i objasni deregistration delay.
```
