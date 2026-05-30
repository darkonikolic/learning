# AI Workflow za DevOps

## Zašto AI menja DevOps workflow

Tradicionalni DevOps zahtjeva pamćenje stotina komandi, sintakse različitih alata i
best practices koji se mijenjaju svakih godinu-dvije. AI ne zamjenjuje to znanje —
ali ubrzava implementaciju i smanjuje "koliko je sintaksa za ovu opciju?" kočnicu.

Razlika je ključna: inženjer koji razumije infrastrukturu + AI koji piše konfiguraciju
je produktivniji tim od inženjera koji samo kopira AI output bez razumijevanja.

**Šta AI mijenja:**
- Pisanje boilerplate koda (Terraform moduli, Helm chartovi, pipeline YAML)
- Debugging nepoznatih errora (paste log, dobij objašnjenje)
- Istraživanje opcija ("koji je best practice za X?")
- Provjera koda kojeg si napisao ("ima li sigurnosnih propusta?")

**Šta AI NE mijenja:**
- Arhitekturne odluke — ti odlučuješ da li VPC treba 2 ili 3 AZ-a
- Razumijevanje infrastrukture — kada pipeline pukne u 3 ujutro, AI neće debugovati umjesto tebe
- Sigurnosne politike — AI predlaže, ali sigurnosni tim (ili ti) potvrđuju
- Produkcione odluke — nikad ne deployas ono što nisi razumio

## CLAUDE.md kao projekt memorija za DevOps

Claude Code čita `CLAUDE.md` pri svakom pokretanju. U DevOps kontekstu, ovaj fajl
treba da sadrži kontekst koji Claude inače ne zna:

```markdown
## Project-A workflow

- Pre svake izmene: /plan → potvrda → egzekucija
- Verzije: Terraform 1.7, EKS 1.29, Helm 3.14, AWS provider ~5.0
- Region: eu-west-1
- EKS cluster: project-a-dev
- S3 state bucket: terraform-state-project-a
- Registry: GitLab Container Registry (ne ECR)
- Load Balancer: AWS ALB Controller (ne nginx ingress)
- Auth: OIDC (ne access keys)

## Terraform validation checklist
- required_version i required_providers pinovani
- Nema secrets u .tf fajlovima
- State je remote (S3 + DynamoDB lock)
- Svaki resurs ima tagove: env, project, owner

## Docker validation checklist
- Pinuj verziju base image-a (:alpine, ne :latest)
- Non-root USER direktiva
- .dockerignore postoji i isključuje .git i .env
```

Svaki put kada Claude odgovori koristeći pogrešan region, pogrešnu verziju providera,
ili pretpostavi nginx ingress umjesto ALB — to je signal da CLAUDE.md treba ažurirati.
Tretaj CLAUDE.md kao živući dokument koji raste zajedno s projektom.

## `/plan` workflow za infrastrukturne promjene

Za DevOps rad, plan-before-execute disciplina je važnija nego ikad:
`terraform apply` na produkciji bez plan reviewa je incident koji čeka da se desi.

Workflow u Claude Code terminalu:

```
# 1. Pokreni plan mode
/plan

# 2. Opiši šta želiš (Claude NE izvršava odmah)
"Treba mi Terraform modul za EKS cluster sa OIDC i Cluster Autoscalerom."

# 3. Claude predlaže plan — provjeri ga
# 4. Potvrdi: "odobravam" ili "izmijeni — hoću X umjesto Y"
# 5. Claude izvršava tek nakon potvrde
```

Ovo je posebno bitno za:
- `terraform apply` — uvijek provjeri plan output ručno prije
- `kubectl delete` ili `helm uninstall` — destruktivne operacije
- Izmjene na produkcijskim security grupama ili IAM politikama

## Hooks kao safety net

U `.claude/settings.json` možeš definisati hooks koji se pokreću automatski.
Primjer: hook koji podsjeća na plan review prije Terraform komandi:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "grep -q 'terraform apply' \"$CLAUDE_TOOL_INPUT\" && echo 'PAUZA: Da li si pregledao terraform plan output?' || true"
          }
        ]
      }
    ]
  }
}
```

Za validacijske hookove (terraform validate, helm lint) — konfiguriši ih kao
`PostToolUse` hookove koji se pokreću automatski posle generisanja koda.

## Tri uloge AI-a u project-A

### 1. Generator

AI piše strukturu koda koji ti opisuješ. Koristiš ga kada:
- Kreiraš novi Terraform modul ("napiši VPC modul sa public/private subnets")
- Pišeš Helm template koji ima mnogo boilerplatea ("napiši Deployment sa svim best practice opcijama")
- Kreiras GitLab CI job koji nisi radio ranije ("napiši job koji radi Trivy scan i failuje na HIGH vulns")

Pravilo generatora: uvijek traži objašnjenje zajedno sa kodom. Prompt
"napiši X" je lošiji od "napiši X i objasni zašto svaki dio postoji".

### 2. Debugger

AI analizira greške koje dobijaš. Koristiš ga kada:
- Pod je u CrashLoopBackOff i ne znaš zašto — prijepi `kubectl describe pod` output
- Terraform apply failuje sa nejasnom greškom — prijepi cijeli error
- GitLab pipeline job failuje — prijepi failed job log

Pravilo debuggera: daj što više konteksta. Ne pitaj "zašto puca?", pitaj
"evo kubectl logs, evo deployment YAML, evo što sam zadnji put promenio — šta nije u redu?"

### 3. Reviewer

AI analizira kod koji si napisao (ili koji je on generisao). Koristiš ga kada:
- Završiš Terraform konfiguraciju — "pregledaj sa sigurnosnog aspekta"
- Napišeš pipeline — "identifikuj bottlenecke i predloži optimizacije"
- Spremaš se za produkciju — "šta može poći po zlu u ovom Helm chartu?"

Pravilo reviewera: budi specifičan o čemu tražiš review. "Pregledaj ovaj kod"
je lošije od "pregledaj ovaj Terraform za: sigurnosne propuste, previsoke troškove,
i sve što bi moglo pući pri terraform destroy".

## Kada NE koristiti AI bez razmišljanja

**Sigurnosne odluke**: AI može predložiti IAM politiku, ali ti moraš razumjeti svaku
permisiju. "Least privilege" nije samo fraza — svaka extra permisija je sigurnosni rizik.

**Produkcione promjene**: AI-generisan `terraform apply` na prod bez plan reviewa je
recept za incident. Uvijek: generiši → razumij → testiraj na dev → primijeni na prod.

**Rotacija secretsa**: AI ne zna tvoje produkcione credentialse (i ne bi trebao).
Pipeline variables, AWS IAM roleovi, kubeconfig — to setup ti, ne AI.

**Arhitektura datastore-a**: Odluka "koristimo RDS vs DynamoDB" ima dugoročne posljedice.
AI može objasniti tradeoff, ali odluka je tvoja sa kontekstom tvog projekta.

**Debugging u produkciji**: AI može biti vodič ("pokušaj ovo"), ali kada sistem gori,
ti moraš razumjeti šta radiš. Nasumično kopiranje AI komandi na prod je opasno.

## AI workflow kroz module project-A

Svaki modul u ovom putu ima AI workflow primjere. Evo pregleda:

| Modul | AI uloga | Primjer |
|-------|----------|---------|
| 01 Docker | Generator | "Napiši multi-stage Dockerfile za nginx sa custom config" |
| 04 Helm | Generator + Reviewer | "Generiši chart, potom pregledaj sa security aspekta" |
| 05 Terraform | Generator + Debugger | "Piši VPC modul" → "Plan failuje, evo errora" |
| 07 Terraform AWS | Generator + Reviewer | EKS modul + cost review |
| 08 Pipelines | Generator + Debugger | Pipeline YAML + failed job debug |
| 09 Monitoring | Generator | "Napiši PrometheusRule za nginx error rate alert" |
| 10 AI DevOps | Sve tri uloge | Ovaj modul — konkretni promptovi |
| 11 Graduation | Sve tri uloge | Kompletan projekt sa AI kroz sve faze |

## Princip: AI nije crna kutija

Svaki put kada koristiš AI output, moraš biti u stanju odgovoriti na:
1. Šta ovaj resurs/konfiguracija radi?
2. Šta se dešava ako ga obrišem/promijenim?
3. Da li ima alternativa i zašto je ovaj pristup bolji?

Ako ne možeš odgovoriti — to je signal da pitaš AI za objašnjenje prije nego što
nastaviš. "Objasni mi ovaj Terraform kod kao da učim infrastrukturu" je sasvim
validan prompt.

## Strukturiranje konteksta za Claude pri DevOps radu

Svaki DevOps prompt treba imati tri dijela:

**1. Šta postoji** (iz CLAUDE.md ili eksplicitno):
```
VPC CIDR: 10.0.0.0/16, private subnets 10.0.1-3.0/24
EKS cluster: project-a-dev, verzija 1.29
Terraform state: s3://terraform-state-project-a
```

**2. Šta trebaš**:
```
Trebaš novi IAM role za GitLab CI/CD sa OIDC autentifikacijom
koji može: describe EKS cluster, helm deploy, čitati S3 state bucket.
```

**3. Ograničenja**:
```
Bez access keys — samo OIDC.
Least privilege — ne "Action": "*".
Terraform format — ne CloudFormation.
```

Što više konteksta daš u CLAUDE.md, to manje ponavljaš u svakom promptu.
