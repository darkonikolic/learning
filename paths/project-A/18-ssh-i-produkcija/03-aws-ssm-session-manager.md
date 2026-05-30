# 03 — AWS SSM Session Manager

## Zašto SSM, Ne SSH

SSH keypair model ima fundamentalne slabosti za timski rad u produkciji:

| Problem sa SSH keypair-om | SSM rješenje |
|--------------------------|--------------|
| Distribucija private key-a između osoba | Nema keypair-a — IAM identitet |
| Port 22 mora biti otvoren (attack surface) | Port 22 zatvoren, nema inbound pravila |
| Keypair treba rotirati | IAM credential rotacija centralizovana |
| Ko je bio na serveru? Teško pratiti | Svaka sesija logirana u CloudTrail + S3 |
| VPN/bastion potreban za private subnet | SSM agent komunicira outbound na SSM endpoint |

**SSM Session Manager** je AWS-nativni način za shell pristup EC2 instancama bez SSH, bez keypair-a, bez otvorenih portova.

---

## Kako SSM Radi

```
Tvoj laptop (aws ssm start-session)
         |
         v
AWS Systems Manager API (HTTPS, port 443)
         |
         v
SSM Agent na EC2 instanci
(outbound konekcija — ne treba inbound port 22)
         |
         v
Shell sesija (tunelirana kroz SSM API)
```

Agent na EC2 inicira outbound konekciju prema SSM service endpoint-u. Tvoj laptop komunicira sa AWS API-jem, ne direktno sa instancom. Rezultat: nema potrebe za otvorenim inbound portom ni bastionom.

---

## Prerekviziti

### 1. SSM Agent na EC2

EKS managed node groups koriste Amazon Linux 2 ili Amazon Linux 2023 AMI — SSM agent je **ugrađen i aktivan by default**.

Provjera:
```bash
# Na EC2 instanci (ako imaš pristup)
systemctl status amazon-ssm-agent

# Ili iz AWS CLI — da li instanca javlja SSM-u
aws ssm describe-instance-information \
  --filters "Key=tag:kubernetes.io/cluster/project-a-prod,Values=owned" \
  --query 'InstanceInformationList[*].[InstanceId,PingStatus,LastPingDateTime]' \
  --output table
```

### 2. IAM Politika za Node (Instance Role)

EKS node IAM role mora imati:
```json
{
  "Effect": "Allow",
  "Action": [
    "ssm:UpdateInstanceInformation",
    "ssmmessages:CreateControlChannel",
    "ssmmessages:CreateDataChannel",
    "ssmmessages:OpenControlChannel",
    "ssmmessages:OpenDataChannel"
  ],
  "Resource": "*"
}
```

Ovo je uobičajeno dio `AmazonSSMManagedInstanceCore` managed policy-ja. U Terraformu:
```hcl
resource "aws_iam_role_policy_attachment" "eks_node_ssm" {
  role       = aws_iam_role.eks_node_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}
```

### 3. AWS CLI Session Manager Plugin

Instalacija lokalno:
```bash
# macOS
brew install --cask session-manager-plugin

# Linux
curl "https://s3.amazonaws.com/session-manager-downloads/plugin/latest/ubuntu_64bit/session-manager-plugin.deb" -o /tmp/ssm-plugin.deb
sudo dpkg -i /tmp/ssm-plugin.deb

# Verifikacija
session-manager-plugin --version
```

---

## Pokretanje SSM Sesije

```bash
# Pronađi instance ID
aws ec2 describe-instances \
  --filters "Name=tag:kubernetes.io/cluster/project-a-prod,Values=owned" \
             "Name=instance-state-name,Values=running" \
  --query 'Reservations[*].Instances[*].[InstanceId,PrivateIpAddress,Tags[?Key==`Name`].Value|[0]]' \
  --output table

# Pokreni sesiju
aws ssm start-session --target i-1234567890abcdef0

# Sada imaš shell na instanci bez SSH!
```

Sesija izgleda ovako:
```
Starting session with SessionId: user@example.com-0abc123def456789
sh-4.2$
```

---

## Port Forwarding Kroz SSM

Ovo je killer feature — pristup privatnim AWS resursima (RDS, ElastiCache) lokalno, bez bastion hosta, bez VPN.

### RDS MySQL kroz SSM

```bash
# Korak 1: Pronađi RDS endpoint
aws rds describe-db-clusters \
  --query 'DBClusters[?DBClusterIdentifier==`project-a-prod`].Endpoint' \
  --output text

# Korak 2: Port forwarding kroz EC2 instancu koja ima mrežni pristup RDS-u
aws ssm start-session \
  --target i-1234567890abcdef0 \
  --document-name AWS-StartPortForwardingSessionToRemoteHost \
  --parameters '{
    "host": ["prod-rds.cluster.eu-west-1.rds.amazonaws.com"],
    "portNumber": ["3306"],
    "localPortNumber": ["13306"]
  }'

# Korak 3: (u drugom terminalu) Spoji se na 127.0.0.1:13306
mysql -h 127.0.0.1 -P 13306 -u admin -p
```

Koristim port `13306` lokalno (ne `3306`) da izbjegnem konflikt sa lokalnim MySQL-om ako ga imaš.

### Redis ElastiCache kroz SSM

```bash
# ElastiCache ne dozvoljava direktan pristup izvan VPC-a
# SSM tunnel to rješava

aws ssm start-session \
  --target i-1234567890abcdef0 \
  --document-name AWS-StartPortForwardingSessionToRemoteHost \
  --parameters '{
    "host": ["project-a-prod.xxxxxx.cache.amazonaws.com"],
    "portNumber": ["6379"],
    "localPortNumber": ["16379"]
  }'

# U drugom terminalu
redis-cli -h 127.0.0.1 -p 16379

# Read-only provjere:
127.0.0.1:16379> INFO server
127.0.0.1:16379> INFO clients
127.0.0.1:16379> DBSIZE
```

**Upozorenje:** SSM port-forward na produkcijsku bazu je **Nivo 3** operacija iz access pyramid-e. Razlog i odobrenje su obavezni.

### Lokalni Port Forwarding (na sam EC2)

```bash
# Pristup aplikaciji koja sluša samo na localhost EC2 instance-a
aws ssm start-session \
  --target i-1234567890abcdef0 \
  --document-name AWS-StartPortForwardingSession \
  --parameters '{"portNumber":["8080"],"localPortNumber":["8080"]}'
```

---

## IAM Politika za Korisnike: Kontrola Ko Može Koristiti SSM

Nije dovoljno da agent radi — korisnik koji pokreće sesiju mora imati IAM dozvolu. I tu je moć SSM-a: granularna kontrola.

### Pristup po tagovima (preporučeno za produkciju)

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowSSMSessionOnDevNodes",
      "Effect": "Allow",
      "Action": "ssm:StartSession",
      "Resource": "arn:aws:ec2:eu-west-1:123456789012:instance/*",
      "Condition": {
        "StringEquals": {
          "ssm:resourceTag/Environment": "dev"
        }
      }
    },
    {
      "Sid": "DenySSMSessionOnProdNodes",
      "Effect": "Deny",
      "Action": "ssm:StartSession",
      "Resource": "arn:aws:ec2:eu-west-1:123456789012:instance/*",
      "Condition": {
        "StringEquals": {
          "ssm:resourceTag/Environment": "prod"
        }
      }
    }
  ]
}
```

`developer` rola može SSM na dev, ne može na prod. `senior-ops` rola može na prod.

### Minimalna politika za port-forward (bez shell pristupa)

```json
{
  "Effect": "Allow",
  "Action": [
    "ssm:StartSession"
  ],
  "Resource": [
    "arn:aws:ssm:eu-west-1:*:document/AWS-StartPortForwardingSessionToRemoteHost"
  ]
}
```

Ovo dozvoljava port-forward ali ne i interaktivni shell.

---

## Audit: Gdje Su Logovi SSM Sesija

### CloudTrail

Svaki `ssm:StartSession` je u CloudTrail:
```
EventName: StartSession
UserIdentity: { "userName": "darko.nikolic" }
RequestParameters: { "target": "i-1234567890" }
ResponseElements: { "sessionId": "darko.nikolic-0abc123..." }
```

### S3 Session Logging (opcionalno, ali preporučeno za prod)

Konfiguracija u SSM → Session Manager → Preferences:
- S3 bucket: `project-a-ssm-session-logs`
- CloudWatch Log Group: `/aws/ssm/sessions`

Ovo snima **kompletnu terminal sesiju** — svaki unos, svaki output.

### Aktivne sesije

```bash
# Ko je trenutno spojen?
aws ssm describe-sessions --state Active

# Prekid sesije (ako treba terminirati)
aws ssm terminate-session --session-id <session-id>
```

---

## SSM vs SSH: Kada Koristiti Šta

| Situacija | Preporuka |
|-----------|-----------|
| Produkcija — shell pristup EC2 | **SSM** |
| Dev — brzo testiranje | SSH može, ali navikni se na SSM |
| Pristup RDS u produkciji | **SSM port-forward** |
| Pristup Redis u produkciji | **SSM port-forward** |
| Automatizovani skripti (CI/CD) | SSM `send-command` ili `run-command` |
| Stari server bez SSM agent-a | SSH kao fallback |
| Emergency, SSM ne radi | EC2 Instance Connect (modul 02) |

---

## Troubleshooting SSM Konekcije

```bash
# Instanca ne javlja se SSM-u
aws ssm describe-instance-information --filters "Key=InstanceIds,Values=i-1234567890"
# Prazna lista = agent ne radi, IAM role nema dozvolu, ili VPC endpoint problem

# Provjera SSM agenta na instanci
sudo systemctl status amazon-ssm-agent
sudo journalctl -u amazon-ssm-agent -n 50

# VPC endpoint (potreban za private subnet bez internet gatewy-a)
aws ec2 describe-vpc-endpoints \
  --filters "Name=service-name,Values=com.amazonaws.eu-west-1.ssm"
# Trebaju biti 3 endpoint-a: ssm, ssmmessages, ec2messages
```

---

## Makefile — dodaj u ovom poglavlju

Ovo poglavlje uvodi SSH pristup i AWS SSM. Dodaj u `Makefile` u korenu projekta:

```makefile
# === OBLAST 18: SSH i produkcija ===

ssm-connect: ## Konekcija na EC2 instancu via AWS SSM (INSTANCE_ID=i-xxx make ssm-connect)
	docker run --rm -it \
	  -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY -e AWS_SESSION_TOKEN \
	  amazon/aws-cli:latest ssm start-session \
	  --target $(INSTANCE_ID) --region $(AWS_REGION)

k-exec: ## Exec shell u pod (POD=xxx NS=dev make k-exec)
	docker run --rm -it \
	  -v ~/.kube:/root/.kube \
	  bitnami/kubectl:$(KUBECTL_VERSION) exec -n $(NS) -it $(POD) -- /bin/sh
```

Centralni Makefile već sadrži ove targete — ovo je referenca šta si dodao u ovoj oblasti.

Provjeri da targeti rade:
```bash
INSTANCE_ID=i-0123456789abcdef0 make ssm-connect
POD=go-service-abc123 NS=dev make k-exec
make help | grep ssm
make help | grep k-exec
```
