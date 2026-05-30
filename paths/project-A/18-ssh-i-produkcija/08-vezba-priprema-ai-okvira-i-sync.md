# 08 — Vežba: priprema AI-okvira i sync (pristup produkciji)

Pripremaš AI-okvir za bezbedan pristup produkciji (SSM/least-privilege umesto otvorenog SSH), pa verifikuješ pristup.

## Cilj

- okvir koji forsira pristup bez trajno otvorenog SSH porta
- dokazano: pristup ide kroz SSM/bastion sa auditom, ne `0.0.0.0/0:22`

## Deo A — Priprema AI-okvira za prod pristup

### A1 — Mapiraj

| Potreba | Postoji? | Gde |
|---------|----------|-----|
| Security persona | da | `/security-trainer` |
| Pristup/incident checklist | delom | `cluster-security-checks` |

### A2 — Odluka (anti-sprawl)

`/system-maintainer` + `process-feedback`: proširi `cluster-security-checks`/`terraform-checks` stavkom „nema otvorenog SSH; SSM Session Manager + audit". Bez novog rule-a ako postojeći pokrivaju.

### A3 — Minimalni dodatak (primer)

```
# dopuna security checks (access)
- Bez SG pravila 0.0.0.0/0 na 22; pristup preko SSM Session Manager.
- Svaki interaktivni pristup logovan (SSM session logging u CloudWatch/S3).
- Privremene, ne trajne, kredencijale (STS) za ljude.
```

## Deo B — Praktičan rad (sync)

### Verifikacija pristupa

```bash
aws ssm start-session --target <instance-id>     # bez SSH ključa/porta
aws ec2 describe-security-groups --query "SecurityGroups[].IpPermissions"   # nema 0.0.0.0/0:22
kubectl exec -it <pod> -- sh                       # za pod-level pristup
```

## Validacija — acceptance kriterijumi

- [ ] odluka A2 doneta preko `/system-maintainer`
- [ ] nema security group pravila `0.0.0.0/0` na portu 22
- [ ] pristup radi preko SSM (bez SSH ključa)
- [ ] sesije se loguju (audit)
- [ ] sync zapisan u `decision_log.md`

## AI workflow

```
Hoću pristup prod instancama bez otvorenog SSH porta.
Objasni SSM Session Manager pristup i šta treba u IAM/SG da to radi sa auditom.
```
