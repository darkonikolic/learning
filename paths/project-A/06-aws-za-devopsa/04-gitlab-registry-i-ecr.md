# GitLab Container Registry i ECR

## GitLab Container Registry kao primarni registry

Project-A koristi GitLab Container Registry (`registry.gitlab.com/user/project`) kao primarni registry za Docker image-e. Ovo je svjesna odluka, ne defaultna.

Svaki push u GitLab repo može automatski buildovati i pushati image:
```
registry.gitlab.com/user/project-a/helloworld:main-a1b2c3d
registry.gitlab.com/user/project-a/helloworld:mr-42-x9y8z7w
registry.gitlab.com/user/project-a/helloworld:latest
```

GitLab automatski autentifikuje CI/CD pipeline prema registriju — nema potrebe za ekstra kredencijalima unutar pipeline-a. Variabla `CI_REGISTRY_PASSWORD` je dostupna automatski.

## Zašto ne ECR za ovaj projekat

AWS ECR je odlična opcija kada:
- Cijeli stack je AWS (ne postoji GitLab)
- Organizacija ima AWS-only policy
- Treba fine-grained image scanning i lifecycle policies

Za project-A ECR dodaje kompleksnost bez benefita:
- Treba IAM rola za push iz CI/CD (ekstra konfiguracija)
- Treba `aws ecr get-login-password` prije svakog pusha
- Uvodi zavisnost: ako nema AWS pristupa, nema builda
- GitLab registry funkcioniše i bez ikakvog AWS naloga (lokalni razvoj)

Princip: manje zavisnosti = manje failure pointa.

## Kako EKS povlači image iz GitLab registrija

EKS worker node-ovi nemaju GitLab kredencijale. Kada Kubernetes scheduluje Pod sa `registry.gitlab.com` image-om, node treba da se autentifikuje.

### Kubernetes Secret tipa docker-registry

```bash
kubectl create secret docker-registry gitlab-registry-secret \
  --docker-server=registry.gitlab.com \
  --docker-username=deploy-token \
  --docker-password=<gitlab-deploy-token> \
  --namespace=helloworld-dev
```

U Deployment manifestu:
```yaml
spec:
  imagePullSecrets:
    - name: gitlab-registry-secret
  containers:
    - name: helloworld
      image: registry.gitlab.com/user/project-a/helloworld:main-a1b2c3d
```

### Terraform kreira Secret u svakom namespace-u

Ručno kreiranje Secreta nije opcija (ne može se reproducirati). Terraform koristi Kubernetes provider:

```hcl
resource "kubernetes_secret" "gitlab_registry" {
  for_each = toset(var.namespaces)

  metadata {
    name      = "gitlab-registry-secret"
    namespace = each.value
  }

  type = "kubernetes.io/dockerconfigjson"

  data = {
    ".dockerconfigjson" = jsonencode({
      auths = {
        "registry.gitlab.com" = {
          username = var.gitlab_deploy_token_username
          password = var.gitlab_deploy_token_password
          auth     = base64encode("${var.gitlab_deploy_token_username}:${var.gitlab_deploy_token_password}")
        }
      }
    })
  }
}
```

`var.gitlab_deploy_token_password` dolazi iz GitLab Project → Settings → Repository → Deploy Tokens. Token ima samo `read_registry` scope — least privilege.

## ECR kao alternativa

Kada tim odluči da pređe na ECR:

1. Push image u ECR: `aws ecr get-login-password | docker login --username AWS ...`
2. EKS node IAM role dobija `ecr:GetDownloadUrlForLayer`, `ecr:BatchGetImage` politiku
3. EKS automatski autentifikuje prema ECR bez imagePullSecrets (isti AWS nalog)
4. Cross-account: EKS u account A, ECR u account B → resource-based policy na ECR

Za enterprise okruženje gdje je sve unutar AWS, ECR je prirodan izbor. Za project-A, GitLab registry je pragmatičniji.

## Image Pull Policy

Kubernetes imagePullPolicy kontrolira kada node povlači image:

| Policy | Ponašanje | Kada koristiti |
|--------|-----------|----------------|
| `Always` | Uvijek kontaktira registry | `latest` tag ili mutable tagovi |
| `IfNotPresent` | Koristi cached ako postoji | Immutable tagovi (git sha) |
| `Never` | Nikad ne povlači | Lokalni development (kind) |

Za project-A: koristiti immutable tagove (git commit SHA) i `IfNotPresent`. Nikad deployovati `latest` u staging/prod — nema traceability šta je zapravo deployovano.

```yaml
image: registry.gitlab.com/user/project-a/helloworld:a1b2c3d4
imagePullPolicy: IfNotPresent
```

Ovo garantuje: isti tag = isti image, uvijek. Nikad "latest je nešto promijenio".
