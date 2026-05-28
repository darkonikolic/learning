# 01 — Produkcijski Pristup: Strategija i Filozofija

## Zašto je ovo drugačije od dev/staging-a

Produkcija nije sandbox. Svaka greška ima realan trošak: korisnici ne mogu koristiti sistem, podaci se mogu izgubiti, reputacija firme strada. SSH ili `kubectl exec` u produkciji nije rutinska operacija — to je hirurški zahvat koji zahtijeva pripremu, oprez i dokumentaciju.

Zlatno pravilo: **ako možeš riješiti problem bez direktnog pristupa produkciji, uradi to bez direktnog pristupa.**

---

## Produkcijski Pristup Pyramid

```
+-------------------------------------------------------+
|  Nivo 4 (iznimno):                                    |
|  SSH na EC2 node (OS-level debug, kernel issues)      |
+-------------------------------------------------------+
|  Nivo 3 (rijetko):                                    |
|  kubectl exec sa write operacijama                    |
|  port-forward na DB                                   |
+-------------------------------------------------------+
|  Nivo 2 (sa razlogom):                                |
|  kubectl exec -it (read-only debugging)               |
+-------------------------------------------------------+
|  Nivo 1 (uvijek OK):                                  |
|  kubectl logs, kubectl describe                       |
|  Grafana, CloudWatch                                  |
+-------------------------------------------------------+
```

### Nivo 1 — Pasivno promatranje (uvijek dozvoljeno)

Nema rizika. Samo čitaš stanje sistema, ne mijenjaš ništa:

- `kubectl logs <pod>` — logovi aplikacije
- `kubectl describe pod/deployment/service` — stanje Kubernetes resursa
- Grafana dashboardi — metriki, alerti
- CloudWatch — AWS-level metriki (RDS, ALB, EKS node CPU/memory)
- `kubectl get events` — šta se događalo u clusteru
- AWS Cost Explorer, CloudTrail — za audit i cost tracking

### Nivo 2 — Aktivno promatranje (potreban razlog)

Ulazak u pod za *read-only* inspekciju. Razlog mora biti dokumentovan:

- `kubectl exec -it <pod> -- sh` sa isključivo read operacijama
- Provjera konfiguracije, proznih fajlova, procesa
- DNS resolution testovi iz pod-a
- Network connectivity provjere

Prije ulaska: zabilježi u incident ticket ili Slack thread zašto ulazaš.

### Nivo 3 — Modifikacije u produkciji (rijetko, oprez)

Ovo je zona gdje se greške dogode. Svaka akcija mora biti premeditated:

- `kubectl exec` pa pisanje u filesystem
- `kubectl port-forward` na bazu podataka za debug query
- `kubectl scale` za hitno skaliranje
- `kubectl rollout restart` za restart servisa

Ovo nije normalan tok — ako redovno trebaš ove operacije, to je signal da tooling nije dobar.

### Nivo 4 — OS-level pristup (iznimno, eskalacija)

SSH direktno na EC2 node koji vrti EKS workload. Opravdano samo za:

- Disk space iscrpljen na node-u (ne može se riješiti iz Kubernetes-a)
- OOM kernel messages koji uzrokuju node eviction
- Network interface problemi na OS nivou
- Container runtime (`containerd`/`crictl`) debug

---

## Audit Trail: Svaka Akcija Mora Biti Traceable

### Kubernetes Audit Log

EKS automatski logira sve API pozive:
- Ko je napravio `kubectl exec`, kada, na koji pod
- Sve create/update/delete operacije
- Dostupno u CloudWatch Logs: `/aws/eks/<cluster-name>/cluster`

### CloudTrail

AWS-level audit za sve akcije:
- Ko je pokrenuo SSM sesiju
- Ko je pristupio Secrets Manager-u
- Ko je mijenjao IAM politike
- Ko je pozivao EKS API

Pretraga u CloudTrail: AWS Console → CloudTrail → Event History

### Praktičan habit

Kad god radiš nešto u produkciji, ostavi trag:
```
# Slack/Teams: "Ulazim u go-service pod u prod, 
# debugiram MySQL connection timeout, ref: INC-123"
kubectl exec -it go-service-7d9f8c-xyz -n project-a-prod -- sh
```

Ovo nije birokracija — to je zaštita za tebe. Ako nešto krene naopako sat vremena kasnije, zna se kontekst.

---

## "Break Glass" Procedura

Scenarij: sve je puklo, pipeline ne radi, alerti zvone, korisnici ne mogu ući. Treba maksimalan pristup odmah.

### Tok akcija

1. **Proglasi incident** — Slack `#incidents`, kreiraj Jira INC ticket
2. **Uzmi snapshot stanja** — CloudWatch, Grafana screenshot, `kubectl get all -n project-a-prod`
3. **Eskalacija odobrenja** — obavijesti team lead / ops lead da uzimas elevated pristup
4. **Akcija sa dokumentacijom** — sve što radiš zapisuješ u incident ticket
5. **Post-incident review** — šta si učinio, zašto, šta treba promijeniti da se ne ponovi

### Break Glass IAM Role

U ozbiljnim timovima postoji zasebna IAM rola `BreakGlassRole` sa punim pristupom, ali:
- Aktivacija šalje SNS notifikaciju svim senior enginerima
- Sve akcije su posebno tagiranu u CloudTrail (`BreakGlass: true`)
- Rola ističe automatski za 1-4 sata

---

## Znak da Tooling Fali

Ako redovno radiš:
- `kubectl exec` za aplikativne operacije (migracije, debug skripte)
- SSH na node da provjeriš logove
- Port-forward na bazu za rutinske upite

...to nije normalno i ne treba to prihvatati. Pravi fix je:

| Problem | Pravi fix |
|---------|-----------|
| `kubectl exec` za log pregled | Centralizovani logging (Loki, ELK) |
| `kubectl exec` za DB query | Read-replica + database GUI tool |
| SSH na node za disk space | K8s resource quotas, persistent volume monitoring |
| Port-forward za Redis debug | Grafana Redis dashboard + alerti |

---

## SSH Keypair Management za EC2

### Kreiranje keypair-a

```bash
# Generisanje keypair-a (van AWS, lokalno)
ssh-keygen -t ed25519 -C "project-a-prod" -f ~/.ssh/project-a-prod

# Ili RSA 4096 ako stariji SSH server
ssh-keygen -t rsa -b 4096 -C "project-a-prod" -f ~/.ssh/project-a-prod
```

Rezultat: `project-a-prod` (private key) + `project-a-prod.pub` (public key)

### Čuvanje i zaštita

```bash
# Private key MORA biti 600 ili 400 — inače SSH odbija konekciju
chmod 400 ~/.ssh/project-a-prod

# Public key ide u AWS → EC2 → Key Pairs (ili Terraform aws_key_pair)
# Private key NIKAD ne izlazi sa tvoje mašine
```

**Zlatna pravila:**
- Jedna osoba = jedan keypair. Nikad ne dijeliti private key.
- Private key NIKAD u git, nikad u email, nikad u Slack
- `~/.ssh/` direktorij treba biti `700`
- Koristiti SSH agent (`ssh-add`) da ne kucaš passphrase svaki put

### Rotacija keypair-a

- Rotacija: svaka 6-12 mjeseci, ili odmah ako sumnja na kompromitovanje
- Proces: kreirati novi keypair → dodati novi public key na sve servere → testirati → ukloniti stari
- Za EKS managed node groups: keypair se mijenja u Launch Template → rolling update node grupe

### Kad keypair nije dovoljan: SSM

Za produkciju preporučujem AWS SSM Session Manager umjesto SSH keypair-a — nema keypair distribucije, nema open port-a 22, sve je logirano u CloudTrail. Detalji u modulu 03.
