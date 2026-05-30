# 09 — Vežba: priprema AI-okvira i sync (AWS osnove)

Pripremaš AI-okvir za rad sa AWS resursima i IAM-om, pa praktično proveravaš pristup i cenu.

## Cilj

- okvir koji pomaže oko IAM least-privilege i procene troška
- dokazano: identitet, dozvole i okvirna cena pre pravljenja resursa

## Deo A — Priprema AI-okvira za AWS

### A1 — Mapiraj

| Potreba | Postoji? | Gde |
|---------|----------|-----|
| DevOps persona | da | `/devops-engineer` |
| Cost/IAM svest | delom | `real-world-focus` (cost awareness) |

### A2 — Odluka (anti-sprawl)

`/system-maintainer` + `process-feedback`: da li dodati skill `aws-cost-check` (procena pre kreiranja) ili je dovoljan `mentor` + cost awareness pravilo. Bez dupliranja — uvedi tek ako se procena ponavlja.

### A3 — Minimalni dodatak (primer)

```
# kandidat skill: aws-cost-check
Input: lista resursa (tip, region, sati/mesec)
Output: gruba mesečna cena + jeftinija alternativa (spot/serverless/manji tip)
```

## Deo B — Praktičan rad (sync)

### Provera identiteta, dozvola i cene

```bash
aws sts get-caller-identity
aws iam simulate-principal-policy --policy-source-arn <arn> --action-names s3:PutObject
# cena: AWS Pricing Calculator ili `aws pricing get-products`
```

## Validacija — acceptance kriterijumi

- [ ] odluka A2 doneta preko `/system-maintainer`
- [ ] `get-caller-identity` potvrđuje očekivani nalog/role
- [ ] IAM simulacija pokazuje least-privilege (nema `*:*`)
- [ ] okvirni mesečni trošak procenjen pre kreiranja
- [ ] sync zapisan u `decision_log.md`

## AI workflow

```
Treba mi IAM policy za [servis] sa minimalnim dozvolama za [akcije].
Daj least-privilege JSON i objasni svaki statement; bez wildcard-a gde nije nužno.
```
