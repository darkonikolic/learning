# 05 — IAM Roles i Permissions kroz AWS Konzolu

## Cilj

Razumjeti IAM strukturu koja je nastala kreiranjem EKS-a i RDS-a, i proširiti je s minimalnim privilegijama za deploy workflow. Naučiti kako IAM mapira na Kubernetes RBAC kroz aws-auth ConfigMap.

---

## Pregled Kreiranog IAM Stanja

Nakon prethodnih modula postoje ovi IAM entiteti:

| IAM Entitet | Tip | Svrha |
|-------------|-----|-------|
| `darko-admin` | IAM User | Svakodnevni rad, konzola, CLI |
| `project-a-dev-eks-cluster-role` | IAM Role | EKS control plane |
| `project-a-dev-node-role` | IAM Role | EC2 worker nodovi |

Budući entiteti (kreiraju se u kasnijim modulima):
- OIDC Role za GitLab CI (modul 08)
- IRSA Role za ESO (External Secrets Operator) — za čitanje Secrets Managera
- IRSA Role za ALB Controller — za kreiranje Load Balancera

---

## Čitanje IAM Policy Dokumenta

Svaka IAM policy je JSON dokument. Osnovna struktura:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "eks:DescribeCluster",
        "eks:ListClusters"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Deny",
      "Action": "ec2:*",
      "Resource": "*"
    }
  ]
}
```

Logika evaluacije:
1. Sve je **Deny** po defaultu
2. Explicit `Allow` otvara pristup
3. Explicit `Deny` uvijek pobjeđuje — čak i ako postoji `Allow` za isti resurs

**Resource ARN wildcards**:
- `*` — sve instance resursa
- `arn:aws:rds:eu-west-1:123456789012:db:project-a-dev-mysql` — tačno jedna RDS instanca
- `arn:aws:rds:eu-west-1:*:db:project-a-dev-*` — sve RDS instance koje počinju s `project-a-dev-`

---

## Kreiranje Custom Deploy Policy

Minimalna prava za Helm deploy na EKS. **Console → IAM → Policies → Create policy**

Izaberi **JSON** tab i unesi:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "EKSDescribe",
      "Effect": "Allow",
      "Action": [
        "eks:DescribeCluster",
        "eks:ListClusters",
        "eks:AccessKubernetesApi"
      ],
      "Resource": "arn:aws:eks:eu-west-1:*:cluster/project-a-dev"
    },
    {
      "Sid": "ECRAccess",
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage"
      ],
      "Resource": "*"
    },
    {
      "Sid": "SecretsRead",
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret"
      ],
      "Resource": "arn:aws:secretsmanager:eu-west-1:*:secret:project-a/dev/*"
    }
  ]
}
```

- Next → **Policy name**: `project-a-dev-deploy-policy`
- Create policy

### Šta ova policy NE dozvoljava

- `ec2:*` — ne može kreirati/brisati EC2 instance
- `rds:DeleteDBInstance` — ne može obrisati bazu
- `iam:*` — privilege escalation nije moguć
- Deploy u `prod` cluster — Resource ARN je ograničen na `project-a-dev`

---

## IAM Role za Developer (Ne Admin)

Developer treba moći deployati ali ne rušiti infrastrukturu.

**IAM → Roles → Create role**

- **Trusted entity**: AWS account → This account
- **Permissions**: attach `project-a-dev-deploy-policy`
- **Role name**: `project-a-dev-deploy-role`
- Create role

Da dodaš developer IAM user-a da može assume ovaj role:

**IAM → Users → developer-user → Add permissions → Create inline policy**:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "sts:AssumeRole",
      "Resource": "arn:aws:iam::123456789012:role/project-a-dev-deploy-role"
    }
  ]
}
```

Developer radi:
```bash
aws sts assume-role \
  --role-arn arn:aws:iam::123456789012:role/project-a-dev-deploy-role \
  --role-session-name deploy-session
```
Dobija privremene credentials (expiraju za 1 sat po defaultu).

---

## EKS aws-auth ConfigMap

Kreirati IAM entitet nije dovoljno. EKS Kubernetes RBAC ne zna za IAM — mapiranje je u `aws-auth` ConfigMap.

Kada se EKS autentikuje zahtjev, tok je:
1. `kubectl` šalje request s AWS SigV4 tokenom
2. `aws-iam-authenticator` (unutar kube-apiserver) validira token kod AWS STS
3. Vraća K8s username/groups na osnovu aws-auth mapiranja
4. K8s RBAC odlučuje ima li taj username/group pravo na akciju

### Pregled aws-auth ConfigMap

```bash
docker run --rm -v ~/.aws:/root/.aws -v ~/.kube:/root/.kube \
  bitnami/kubectl:1.29 get configmap aws-auth -n kube-system -o yaml
```

Vidjećeš automatski dodana mapiranja za Node Group role. Izgleda ovako:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: aws-auth
  namespace: kube-system
data:
  mapRoles: |
    - rolearn: arn:aws:iam::123456789012:role/project-a-dev-node-role
      username: system:node:{{EC2PrivateDNSName}}
      groups:
        - system:bootstrappers
        - system:nodes
```

### Dodavanje IAM User-a kao Cluster Admin

```bash
docker run --rm -v ~/.aws:/root/.aws -v ~/.kube:/root/.kube \
  bitnami/kubectl:1.29 edit configmap aws-auth -n kube-system
```

Dodaj pod `mapRoles:` sekciju novu `mapUsers:` sekciju:

```yaml
  mapUsers: |
    - userarn: arn:aws:iam::123456789012:user/darko-admin
      username: darko-admin
      groups:
        - system:masters
```

`system:masters` je K8s built-in group s cluster-admin pravima. Za developer role koristi manje privilegovanu grupu ili kreiraj custom ClusterRole.

**Spremi i izađi** (`:wq` u vim, ili `Ctrl+X` u nano ovisno o editoru).

### Dodavanje Deploy Role u aws-auth

Za `project-a-dev-deploy-role`:

```yaml
  mapRoles: |
    - rolearn: arn:aws:iam::123456789012:role/project-a-dev-node-role
      username: system:node:{{EC2PrivateDNSName}}
      groups:
        - system:bootstrappers
        - system:nodes
    - rolearn: arn:aws:iam::123456789012:role/project-a-dev-deploy-role
      username: deploy-role
      groups:
        - deploy-group
```

Pa kreiraj K8s ClusterRoleBinding za `deploy-group`:

```yaml
# deploy-rbac.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: deploy-group-binding
subjects:
  - kind: Group
    name: deploy-group
    apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: ClusterRole
  name: edit  # K8s built-in: može deploy/update, ne može delete namespace
  apiGroup: rbac.authorization.k8s.io
```

---

## Česta IAM Greška: "You don't have permission to access this cluster"

**Simptom**: `kubectl get nodes` vraća `error: You must be logged in to the server (Unauthorized)`

**Uzrok 1**: IAM user/role nije u aws-auth ConfigMap.
- Provjeri: `aws sts get-caller-identity` — koji ARN koristiš?
- Provjeri aws-auth — ima li taj ARN mapiranje?

**Uzrok 2**: Access key koji koristiš ne odgovara IAM user-u koji je u aws-auth.
- `aws configure list` — koji profil je aktivan?

**Uzrok 3**: Cluster creator (IAM entitet koji je kliknuo Create u konzoli) automatski dobija system:masters pristup, ali **samo taj entitet**. Ako si kreirao cluster kao `darko-admin` a pokušavaš se spojiti kao `darko-admin-cli` (drugi access key, isti user) — radi. Ako pokušavaš kao drugi IAM user — nema pristupa dok ga ne dodaš u aws-auth.

---

## IAM Access Analyzer

**Console → IAM → Access Analyzer → Create analyzer**

- **Analyzer name**: `project-a-dev-analyzer`
- **Zone of trust**: Current account
- Create

Analyzer skenira sve resource-based policy-je i IAM policy-je u accountu te traži:
- External access (pristup van tvog accounta)
- Unused permissions (policy dopušta akciju koja se nikad ne koristi)

Findings se pojavljuju u: **Access Analyzer → Findings**

Za svaki finding možeš: Archive (svjesno prihvataš rizik) ili Resolve (fix policy).

**Pokretanje analize od nule**:
```bash
docker run --rm -v ~/.aws:/root/.aws amazon/aws-cli:latest \
  accessanalyzer list-findings \
  --analyzer-arn arn:aws:access-analyzer:eu-west-1:123456789012:analyzer/project-a-dev-analyzer \
  --query 'findings[?status==`ACTIVE`].[id,resourceType,condition]' \
  --output table
```
