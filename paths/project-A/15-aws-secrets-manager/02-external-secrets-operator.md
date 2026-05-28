# 02 — External Secrets Operator

## Zašto ESO umjesto direktnog čitanja iz aplikacije

Naivni pristup: aplikacija direktno poziva AWS SDK da pročita secret pri startu:

```go
// Anti-pattern: aplikacija direktno čita SM
func getDBPassword() string {
    svc := secretsmanager.New(session.Must(session.NewSession()))
    result, err := svc.GetSecretValue(&secretsmanager.GetSecretValueInput{
        SecretId: aws.String("/project-a/prod/rds/app-user-password"),
    })
    // ...
}
```

Problemi ovog pristupa:

1. **AWS SDK dependency u svakom servisu:** Go service, PHP service, buduće servise — svi moraju implementirati SM client, error handling, retry logiku, caching (da ne bi gadam API-a).

2. **IRSA complexity per pod:** Svaki pod treba svoju IRSA konfiguraciju. PHP service koji treba 3 secrets i Go service koji treba 5 secrets — svaki ima vlastitu IAM rolu, vlastiti token mount, vlastitu konfiguraciju.

3. **Nema auto-refresh bez restart:** Ako SM secret se rotira, aplikacija mora biti restarted ili mora implementirati vlastiti refresh mehanizam.

4. **Vendor lock-in u application code:** Ako sutra prelazite na Vault ili Azure Key Vault, morate mijenjati aplikacijski kod.

5. **Secret nije vidljiv K8s toolingom:** Helm chart koji deploya aplikaciju ne može raditi `valueFrom.secretKeyRef` ako secrets nisu K8s Secret objekti.

**ESO rješava sve ovo:** Jedan controller u klasteru čita SM i kreira standardne K8s Secrets. Aplikacija ne zna odakle credentials dolaze.

---

## Kako ESO funkcioniše — tok podataka

```
AWS Secrets Manager
        ↑ GetSecretValue (IRSA)
        |
ESO Controller (pod u klasteru)
        |
        ↓ create/update
K8s Secret (enkriptovan u etcd ako EKS envelope encryption uključen)
        |
        ↓ secretKeyRef / envFrom
Aplikacijski pod (čita kao env var ili volume mount)
```

ESO controller watch-uje `ExternalSecret` CRD objekte. Kada pronađe novi ili kada istekne `refreshInterval`, poziva SM API (koristeći IRSA credentials), i kreira/ažurira odgovarajući K8s Secret.

---

## Terraform: instalacija ESO via Helm

```hcl
# terraform/modules/eks-addons/eso.tf

resource "helm_release" "external_secrets" {
  name             = "external-secrets"
  repository       = "https://charts.external-secrets.io"
  chart            = "external-secrets"
  version          = "0.9.13"  # Pinuj verziju
  namespace        = "external-secrets"
  create_namespace = true

  set {
    name  = "serviceAccount.annotations.eks\\.amazonaws\\.com/role-arn"
    value = aws_iam_role.eso_irsa.arn
  }

  set {
    name  = "installCRDs"
    value = "true"
  }

  # Production: 3 replike za HA
  set {
    name  = "replicaCount"
    value = var.environment == "prod" ? "3" : "1"
  }

  depends_on = [aws_eks_cluster.main, aws_iam_role_policy_attachment.eso_irsa]
}
```

---

## IRSA za ESO

ESO controller treba IAM rolu da bi čitao iz SM. Princip least privilege: čita samo secrets za svoju okolinu.

```hcl
# terraform/modules/eks-addons/eso-iam.tf

data "aws_iam_policy_document" "eso_assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.eks.arn]
    }

    condition {
      test     = "StringEquals"
      variable = "${replace(aws_iam_openid_connect_provider.eks.url, "https://", "")}:sub"
      values   = ["system:serviceaccount:external-secrets:external-secrets"]
    }

    condition {
      test     = "StringEquals"
      variable = "${replace(aws_iam_openid_connect_provider.eks.url, "https://", "")}:aud"
      values   = ["sts.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "eso_irsa" {
  name               = "project-a-${var.environment}-eso-irsa"
  assume_role_policy = data.aws_iam_policy_document.eso_assume_role.json
}

data "aws_iam_policy_document" "eso_secrets_policy" {
  statement {
    effect = "Allow"
    actions = [
      "secretsmanager:GetSecretValue",
      "secretsmanager:DescribeSecret",
    ]
    # Samo secrets za ovu okolinu
    resources = [
      "arn:aws:secretsmanager:${var.aws_region}:${data.aws_caller_identity.current.account_id}:secret:/project-a/${var.environment}/*"
    ]
  }
}

resource "aws_iam_role_policy" "eso_secrets" {
  name   = "eso-secrets-access"
  role   = aws_iam_role.eso_irsa.id
  policy = data.aws_iam_policy_document.eso_secrets_policy.json
}
```

---

## SecretStore CRD

`SecretStore` definiše konekciju prema SM. Kreira se jednom po namespace-u (ili `ClusterSecretStore` za cluster-wide):

```yaml
# k8s/base/external-secrets/secret-store.yaml
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: aws-secrets-manager
  namespace: project-a
spec:
  provider:
    aws:
      service: SecretsManager
      region: eu-west-1
      auth:
        jwt:
          serviceAccountRef:
            name: external-secrets-sa
            # ESO kreira ovaj SA i binduje ga na IRSA rolu
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: external-secrets-sa
  namespace: project-a
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::123456789012:role/project-a-prod-eso-irsa
```

---

## ExternalSecret CRD primjeri za project-a

### Go service — DB credentials

```yaml
# k8s/apps/go-service/external-secret-db.yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: go-service-db-credentials
  namespace: project-a
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secrets-manager
    kind: SecretStore
  target:
    name: go-service-db-credentials
    creationPolicy: Owner
    # Owner policy: ESO posjeduje K8s Secret — briše ga ako ExternalSecret se obriše
    template:
      engineVersion: v2
      data:
        # Možete transformisati format: SM čuva JSON, K8s Secret dobija individual keys
        DB_DSN: "{{ .username }}:{{ .password }}@tcp({{ .host }}:3306)/{{ .dbname }}?parseTime=true&tls=true"
  data:
    - secretKey: username
      remoteRef:
        key: /project-a/prod/rds/app-user-password
        property: username   # SM secret je JSON: {"username": "appuser", "password": "..."}
    - secretKey: password
      remoteRef:
        key: /project-a/prod/rds/app-user-password
        property: password
    - secretKey: host
      remoteRef:
        key: /project-a/prod/rds/app-user-password
        property: host
    - secretKey: dbname
      remoteRef:
        key: /project-a/prod/rds/app-user-password
        property: dbname
```

### Go service — Redis + JWT

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: go-service-secrets
  namespace: project-a
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secrets-manager
    kind: SecretStore
  target:
    name: go-service-secrets
    creationPolicy: Owner
  data:
    - secretKey: REDIS_AUTH_TOKEN
      remoteRef:
        key: /project-a/prod/redis/auth-token
    - secretKey: JWT_SECRET
      remoteRef:
        key: /project-a/prod/go-service/jwt-secret
```

### PHP service — session secret

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: php-service-secrets
  namespace: project-a
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secrets-manager
    kind: SecretStore
  target:
    name: php-service-secrets
    creationPolicy: Owner
  data:
    - secretKey: SESSION_SECRET
      remoteRef:
        key: /project-a/prod/php-service/session-secret
    - secretKey: REDIS_AUTH_TOKEN
      remoteRef:
        key: /project-a/prod/redis/auth-token
```

---

## Korištenje K8s Secrets u Deploymentu

```yaml
# k8s/apps/go-service/deployment.yaml (relevantni dio)
spec:
  template:
    spec:
      containers:
        - name: go-service
          envFrom:
            - secretRef:
                name: go-service-secrets  # Kreira ESO
          env:
            - name: DB_DSN
              valueFrom:
                secretKeyRef:
                  name: go-service-db-credentials
                  key: DB_DSN
```

---

## Auto-refresh i rolling restart

Kada SM secret se rotira, ESO ažurira K8s Secret unutar `refreshInterval`. Ali **K8s ne restartuje podove automatski** kada se Secret promijeni — env vars su baked in pri startu poda.

Rješenje: Reloader controller (Stakater Reloader):

```hcl
# terraform/modules/eks-addons/reloader.tf
resource "helm_release" "reloader" {
  name       = "reloader"
  repository = "https://stakater.github.io/stakater-charts"
  chart      = "reloader"
  version    = "1.0.69"
  namespace  = "reloader"
  create_namespace = true
}
```

```yaml
# Deploymentu dodati annotation:
metadata:
  annotations:
    secret.reloader.stakater.com/reload: "go-service-secrets,go-service-db-credentials"
```

Sada: SM rotacija → ESO ažurira K8s Secret → Reloader detektuje promjenu → rolling restart Deployments koji koriste taj Secret. Zero-downtime rotacija.

---

## Gotche i failure modes

**refreshInterval previše agresivan:**  
`refreshInterval: 1m` na clusteru sa 50 ExternalSecrets = 50 SM API poziva/minuti = troškovi i throttling. Koristiti `1h` za passwords, `24h` za rijetko-mijenjane secrets.

**SecretStore bez namespace isolation:**  
`ClusterSecretStore` (cluster-wide) znači da ExternalSecret u bilo kojem namespace-u može čitati bilo koji SM secret. Koristiti namespace-scoped `SecretStore` sa IRSA rolom ograničenom na taj namespace.

**creationPolicy: Merge vs Owner:**  
`Merge` ne briše K8s Secret kada ExternalSecret se obriše — može ostaviti stale credentials. Koristiti `Owner` u produkciji.

**SM secret format — String vs Binary:**  
ESO očekuje JSON string format za `property` lookup. Ako SM secret je plain string (ne JSON), morate izostaviti `property` polje. Konzistentno koristiti JSON format za sve SM secrets.

**Reloader i stateful aplikacije:**  
Rolling restart funkcioniše za stateless servise. Za Go service sa in-flight requestima koji traju dugo, konfigurišite `preStop` hook i `terminationGracePeriodSeconds` adekvatno.
