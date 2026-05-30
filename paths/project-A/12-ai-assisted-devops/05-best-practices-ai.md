# Best Practices za AI u DevOps-u (Claude Code)

## Principi za CLAUDE.md authoring

`CLAUDE.md` je primarni mehanizam za davanje trajnog konteksta Claudeu. Dobro napisan
`CLAUDE.md` znači da ne ponavljaš iste informacije u svakom promptu.

**Šta ide u CLAUDE.md:**
- Verzije alata specifične za projekt (Terraform 1.7, EKS 1.29, AWS provider ~5.0)
- Cloud provider specifičnosti (region, networking model, load balancer tip)
- Existing resursi (VPC CIDR, cluster name, S3 bucket nazivi)
- Ograničenja i constraint-i (ne access keys, ne nginx ingress, OIDC only)
- Validation checklist-e po oblasti (Terraform, Docker, K8s, pipeline)
- Project-A workflow pravila (plan→egzekucija→validacija petlja)

**Šta NE ide u CLAUDE.md:**
- Secrets i credentialsi — nikada
- Produkcioni endpoint-i i IP adrese (sigurnosni rizik)
- Privremene odluke koje će se promijeniti za par dana
- Opšte znanje koje Claude već ima (ne trebaš objašnjavati šta je Docker)
- Previše detaljna pravila — CLAUDE.md postaje nepregledan

**Princip anti-sprawl:** Dodaj sekciju u CLAUDE.md samo kada se ista potreba
pojavi kroz dva ili više modula. Jedna vježba ne opravdava novu sekciju.

**Primjer dobre CLAUDE.md sekcije:**
```markdown
## Terraform validation checklist
- required_version i required_providers pinovani (bez ~> Latest ili bez verzije)
- Nema secrets u .tf/.tfvars koji se commit-uju — koristi variable bez default-a
- Svaki resurs: tagovi env, project, owner
- State je remote (S3 + DynamoDB lock)
- Moduli imaju source sa pinovanom verzijom ili lokalnim relativnim putem
```

## Plan before execute disciplina

`/plan` nije opcija — za infrastrukturni rad je obavezan korak.

**Kada UVIJEK koristiti `/plan`:**
- Prije bilo koje `terraform apply`
- Prije `kubectl delete`, `helm uninstall`, `helm rollback`
- Prije izmjena IAM politika ili security group pravila
- Prije produkcijskog deploya

**Kada možeš ići direktno (bez /plan):**
- Čitanje stanja: `kubectl get pods`, `terraform show`, `helm list`
- Lokalni razvoj i testiranje (kind cluster, docker-compose)
- Generisanje boilerplate koda koji ćeš ručno pregledati prije primjene
- Debugging koji ne mijenja stanje

**Workflow:**
```
/plan
→ opiši šta trebaš
→ Claude predlaže plan
→ ti pregledaš
→ potvrdiš ili tražiš izmjenu
→ Claude izvršava tek nakon potvrde
```

## Kontekst management — token budžet

Claude ima ograničen context window. U dugim razgovorima, starije poruke "ispadaju".

**Praktične posljedice za DevOps:**
- Nemoj lijepiti cijeli `terraform.tfstate` u chat — samo relevantne dijelove
- Ako razgovor postaje dug, počni novi i ponovi ključni kontekst
- `terraform plan` output od 500 linija — izreži relevantne dijelove ili pitaj Claude da fokusira
- Koristi CLAUDE.md za trajni kontekst umjesto ponovnog lijepljenja

**Šta lijepiti u Claude:**
```
# Dobar kontekst — fokusiran
Ovaj terraform plan output ima 200 linija. Interesuje me samo dio koji se tiče
EKS node groupa — evo tih 20 linija: [...]

# Loš kontekst — previše
[lijepim cijeli 500-linijski plan output]
```

## Trust but verify — uvijek provjeri AI output

Zlatno pravilo: nikad ne deployas AI-generisan kod direktno na produkciju bez
da ga razumiješ i testiraš.

**Pipeline za svaki AI-generisan Terraform:**
```bash
# Korak 1: Validacija sintakse
terraform validate

# Korak 2: Formatiranje (da je konzistentno)
terraform fmt -diff

# Korak 3: Statička analiza
docker run --rm -v $(pwd):/src aquasec/tfsec /src --no-color

# Korak 4: Plan review — čitaj output liniju po liniju
terraform plan -out=tfplan

# Korak 5: Provjeri destruktivne promjene
terraform show -json tfplan | \
  jq '.resource_changes[] | select(.change.actions | contains(["delete"]))'

# Tek nakon što razumiješ svaku liniju plana:
terraform apply tfplan
```

**Za AI-generisan Kubernetes manifest:**
```bash
# Provjeri sigurnost
docker run --rm -v $(pwd):/data kubesec/kubesec:latest scan /data/deployment.yaml

# Dry run na klasteru
kubectl apply --dry-run=client -f deployment.yaml

# Provjeri diff ako resource već postoji
kubectl diff -f deployment.yaml
```

**Znakovi zastarjelog AI savjeta:**
- Koristi `apiVersion: extensions/v1beta1` (deprecated u K8s 1.22+)
- Preporučuje `kubectl create serviceaccount` bez IRSA za AWS permisije
- Koristi `eksctl` gdje Terraform ima bolji native support
- Generisani IAM policy ima `"Action": "*"` ili `"Resource": "*"`

## Institutional memory u CLAUDE.md

Tokom projekta, CLAUDE.md treba rasti zajedno s tvojim učenjem. Svaki put kada:
- Nađeš da AI pravi istu grešku — dodaj pravilo koje to sprječava
- Naučiš koji AWS pattern koristiti — zapiši ga kao kontekst
- Doneseš arhitekturnu odluku — zapiši razlog (ne samo odluku)

**Primjer evoluiranja CLAUDE.md:**

Sedmica 1 — minimalan:
```markdown
## Project-A workflow
- /plan prije svake izmene
- Region: eu-west-1
```

Sedmica 4 — bogat kontekstom:
```markdown
## Project-A workflow
- /plan prije svake izmene
- Region: eu-west-1
- EKS: project-a-dev (1.29), managed node groups, OIDC aktivan
- Load Balancer: AWS ALB Controller — ne nginx ingress (odluka: ALB native integracija sa ACM)
- Terraform state: s3://terraform-state-project-a, lock: dynamodb terraform-locks
- GitLab runner: u VPC-u (private subnet) — EKS private endpoint radi

## Lekcije naučene
- EKS security groups: node group SG mora dozvoliti 443 prema cluster SG
- Helm --wait timeout: 5m minimalno na sporim nodovima
- terraform fmt mora biti u pre-commit hook — CI failuje bez toga
```

## Hooks kao safety net

`.claude/settings.json` hookovi su automatski pokrenutih validacija.
Za DevOps, korisni primjeri:

**Pre-apply reminder:**
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "echo $CLAUDE_TOOL_INPUT | grep -q 'terraform apply' && echo '⚠️  Jesi li pregledao terraform plan?' || true"
          }
        ]
      }
    ]
  }
}
```

**Post-generate validation** (pokretanje helmlint nakon generisanja chart-a):
Hookovi se mogu koristiti za automatsku validaciju bez da moraš ručno pozivati
alate svaki put. Detalji konfiguracije su u `claude /help hooks`.

## Prompt Engineering za DevOps

### Budi specifičan sa verzijama

Loše:
```
Napiši Terraform za EKS.
```

Dobro:
```
Napiši Terraform 1.7 za EKS 1.29 koristeći AWS provider ~5.0.
Managed node group sa t3.medium, OIDC provider, Cluster Autoscaler IRSA.
Region eu-west-1. VPC ID dolazi kao varijabla.
Objasni svaki resurs i zašto postoji.
```

### Traži objašnjenja uz kod

Svaki AI prompt za generisanje koda treba imati:
```
... i objasni:
1. Zašto svaki resurs postoji
2. Šta se dešava ako ga obrišem
3. Koji su tradeoffs ovog pristupa
```

### Sigurnosni review kao odvojeni korak

Ne pitaj "napiši sigurno" — pitaj odvojeno:
```
Evo finalne verzije ovog [Terraform/Helm/pipeline].
Uradi sigurnosni review i identificiraj:
- Svaki resurs/konfiguracija koja ima preširoke permisije
- Secreti koji mogu biti exposed u logovima
- Konfiguracije koje su OK za dev ali loše za prod
```

## Granice AI znanja

**Knowledge cutoff**: AI ima datum do kojeg zna informacije. Za AWS servise koji se
brzo mijenjaju (EKS, ALB annotations), uvijek provjeri aktuelnu dokumentaciju.

**Hallucinated API calls**: AI može izmisliti Terraform resource argumente koji
ne postoje. Uvijek provjeri `terraform validate`.

**Regionalne razlike**: AI može generisati kod koji radi u us-east-1 ali ne u
eu-west-1 (dostupnost instance tipova, AMI ID-ovi). Zato je region u CLAUDE.md.

## AI u timu

**Code review AI-generisanog koda**: Kada radiš PR sa AI-generisanim kodom,
naznači to u PR opisu. Revieweri trebaju znati da posebno paze na:
- Logiku koja izgleda ispravna ali ima subtilnu grešku
- Sigurnosne implikacije koje AI nije uočio
- Troškove koji nisu očigledni iz koda

**Dijeli promptove**: Ako nađeš dobar prompt koji generiše kvalitetan kod,
podijeli sa timom. "Evo prompta kojim sam generisao EKS modul" je vrijedno znanje.

**Veza sa project-A:**

Kroz modul 11, svaki put kada koristiš AI:
1. Uključi verzije iz ovog projekta (iz CLAUDE.md)
2. Koristi `/plan` prije destruktivnih operacija
3. Traži objašnjenje uz svaki generisani kod
4. Provjeri sa `terraform validate` / `kubectl dry-run` / `helm lint`
5. Nikad ne applyuj na prod bez dev testa
