# 02 — SSH na EC2 i EKS Nodove

## Kada Ti Treba SSH na EKS Node

EKS node je EC2 instanca koja vrti Kubernetes. U 95% slučajeva, problem koji imaš rješavaš kroz Kubernetes API (`kubectl`), ne kroz SSH. Ali postoji ostatak:

**Legitimni razlozi za SSH na EKS node:**

| Problem | Zašto SSH |
|---------|-----------|
| Disk space iscrpljen (`/var/lib/containerd`) | Ne može se vidjeti/riješiti iz Kubernetes-a |
| `dmesg` / `journalctl` za OOM kernel eviction | OS-level logovi |
| Network interface debug (`ip addr`, `tcpdump`) | Kubernetes ne eksponira ovo |
| `containerd`/`crictl` problemi — container runtime crash | Ispod Kubernetes API-a |
| Node NotReady i `kubelet` se ne pokreće | `systemctl status kubelet` |

**Nije razlog za SSH:**
- Gledanje application logova (koristi `kubectl logs`)
- Provjera ENV varijabli (koristi `kubectl describe pod`)
- Restart aplikacije (koristi `kubectl rollout restart`)
- Provjera konfiguracije (koristi `kubectl exec`)

---

## EC2 Key Pair: Osnove

### Kreiranje i priprema

```bash
# Kreiraj lokalno (preporučeno nad AWS-generisanim)
ssh-keygen -t ed25519 -C "project-a-prod-$(date +%Y%m)" -f ~/.ssh/project-a-prod

# Zaštiti private key
chmod 400 ~/.ssh/project-a-prod

# Provjeri fingerprint (za verifikaciju)
ssh-keygen -l -f ~/.ssh/project-a-prod.pub
```

### Registracija u AWS

```bash
# Import public key u AWS (Terraform to radi automatski, ali ručno je moguće)
aws ec2 import-key-pair \
  --key-name "project-a-prod" \
  --public-key-material fileb://~/.ssh/project-a-prod.pub \
  --region eu-west-1
```

U Terraformu:
```hcl
resource "aws_key_pair" "project_a_prod" {
  key_name   = "project-a-prod"
  public_key = file("~/.ssh/project-a-prod.pub")
}
```

---

## SSH na EKS Node Direktno (Samo Dev/Test)

Za dev cluster gdje su nodovi u public subnet-u:

```bash
# Pronađi public IP EKS node-a
kubectl get nodes -o wide
# EXTERNAL-IP kolona

# SSH pristup
ssh -i ~/.ssh/project-a-dev.pem ec2-user@<node-public-ip>

# Ili sa user datom za Amazon Linux 2023:
ssh -i ~/.ssh/project-a-dev.pem ec2-user@3.123.45.67
```

**Napomena:** EKS managed nodes koriste `ec2-user` na Amazon Linux 2/2023, `ubuntu` na Ubuntu AMI-u.

**Ovo NIKAD ne raditi u produkciji** — prod nodovi su u private subnet-u bez public IP-a. Direktan SSH nije moguć bez bastion hosta ili SSM.

---

## Bastion Host Pattern za Produkciju

Produkcijska arhitektura: EKS nodovi su u private subnet-u. Potreban je "most" (jump server) u public subnet-u.

```
Internet
    |
    v
+------------------+       +------------------+
|  Bastion Host    | SSH → |  EKS Node        |
|  (public subnet) |       |  (private subnet) |
|  10.0.0.10       |       |  10.0.3.50       |
|  public: 1.2.3.4 |       |  no public IP    |
+------------------+       +------------------+
```

### SSH Config za Jump Host

Uredi `~/.ssh/config`:

```
# Bastion host (ulazna tačka)
Host bastion-prod
  HostName 1.2.3.4
  User ec2-user
  IdentityFile ~/.ssh/project-a-prod.pem
  ServerAliveInterval 60
  ServerAliveCountMax 3

# EKS node kroz bastion (ProxyJump)
Host eks-node-prod
  HostName 10.0.3.50
  User ec2-user
  IdentityFile ~/.ssh/project-a-prod.pem
  ProxyJump bastion-prod
```

```bash
# Konekcija na EKS node (transparentno kroz bastion)
ssh eks-node-prod

# SSH agent forwarding (za dalje skokove bez kopiranja key-a na bastion)
ssh -A eks-node-prod
```

### Pronalaženje Private IP-a EKS Node-a

```bash
# Iz kubectl
kubectl get nodes -o wide
# INTERNAL-IP kolona = private IP

# Ili iz AWS CLI
aws ec2 describe-instances \
  --filters "Name=tag:kubernetes.io/cluster/project-a-prod,Values=owned" \
  --query 'Reservations[*].Instances[*].[PrivateIpAddress,InstanceId,State.Name]' \
  --output table
```

---

## AWS EC2 Instance Connect (Emergency Pristup)

Scenarij: keypair izgubljen ili SSH config ne radi. EC2 Instance Connect omogućava one-time SSH bez trajnog keypair-a:

```bash
# Korak 1: Generiši temporary keypair
ssh-keygen -t ed25519 -f ~/.ssh/temp-emergency -N ""

# Korak 2: Push public key na instancu (važi 60 sekundi)
aws ec2-instance-connect send-ssh-public-key \
  --instance-id i-1234567890abcdef0 \
  --instance-os-user ec2-user \
  --ssh-public-key file://~/.ssh/temp-emergency.pub \
  --region eu-west-1

# Korak 3: SSH odmah (60-sekundi prozor)
ssh -i ~/.ssh/temp-emergency ec2-user@<public-or-private-ip>
```

**Uslovi:** instanca mora imati Instance Connect endpoint ili biti u public subnet-u. Za private subnet: EC2 Instance Connect Endpoint (zasebna konfiguracija).

**Sigurnost:** ova akcija se logira u CloudTrail. Emergency, ne rutina.

---

## Na EKS Node-u: Šta Radiš Nakon Pristupa

### Container Runtime Debug

```bash
# Koji containeri rade na ovom node-u
sudo crictl ps

# Logovi specifičnog containera (ID iz crictl ps)
sudo crictl logs <container-id>

# Detalji containera
sudo crictl inspect <container-id>

# Slika (image) info
sudo crictl images
```

### Kubelet Status

```bash
# Da li kubelet radi?
systemctl status kubelet

# Kubelet logovi (zadnjih 100 linija)
journalctl -u kubelet -n 100

# Kubelet logovi od zadnjeg boota
journalctl -u kubelet -b
```

### Disk Space Debug

```bash
# Ukupno
df -h

# Containerd storage (česti krivac)
du -sh /var/lib/containerd/

# Docker (ako se koristi, stariji setup)
du -sh /var/lib/docker/

# Čišćenje nekorištenih image-a (oprez u produkciji!)
sudo crictl rmi --prune
```

### Network Debug

```bash
# Network interface-i
ip addr show

# Routing tabla
ip route show

# Da li node može dosegnuti API server?
curl -k https://<eks-api-endpoint>/healthz

# iptables pravila (CNI plugin ih koristi)
sudo iptables -L -n | head -50
```

### OOM Debug

```bash
# OOM kill u kernel logu
dmesg | grep -i "oom\|killed process"

# Ili kroz journalctl
journalctl -k | grep -i oom
```

---

## Sigurnost: Šta Napraviti Nakon SSH Sesije

1. **Izloguj se** — ne ostavljaj otvorene sesije (`exit` ili `logout`)
2. **Zabilježi šta si radio** — update incident ticket
3. **Provjeri da nisi ostavio privremene fajlove** — `/tmp`, home direktorij na bastionu
4. **Ako si koristio SSH agent forwarding** — `ssh-add -D` da ukloniš ključeve iz agenta
5. **Revoke temp keypair** — ako si koristio EC2 Instance Connect, temp key ionako ističe, ali obriši lokalno:
   ```bash
   rm ~/.ssh/temp-emergency ~/.ssh/temp-emergency.pub
   ```
