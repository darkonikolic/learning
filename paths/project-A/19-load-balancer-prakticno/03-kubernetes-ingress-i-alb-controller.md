# 03 — Kubernetes Ingress i AWS Load Balancer Controller

## Preduslovi

Prije instalacije ALB Controllera treba:

1. **OIDC provider** za EKS cluster (omogućava IRSA)
2. **IAM Policy** sa permisijama za kreiranje ALB resursa
3. **IAM Role** vezana za K8s Service Account (IRSA)

---

## Korak 1: OIDC Provider i IAM Setup

```bash
# Provjeri da li OIDC provider već postoji
aws iam list-open-id-connect-providers | grep $(aws eks describe-cluster \
  --name project-a-dev \
  --query "cluster.identity.oidc.issuer" \
  --output text | sed 's|https://||')

# Ako ne postoji, kreiraj ga
eksctl utils associate-iam-oidc-provider \
  --region eu-west-1 \
  --cluster project-a-dev \
  --approve
```

```bash
# Preuzmi AWS managed policy za ALB Controller
curl -O https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/v2.7.0/docs/install/iam_policy.json

# Kreiraj IAM policy
aws iam create-policy \
  --policy-name AWSLoadBalancerControllerIAMPolicy \
  --policy-document file://iam_policy.json

# Spremi ARN
POLICY_ARN=$(aws iam list-policies \
  --query 'Policies[?PolicyName==`AWSLoadBalancerControllerIAMPolicy`].Arn' \
  --output text)

# Kreiraj IAM Role i Service Account vezanu za nju (IRSA)
eksctl create iamserviceaccount \
  --cluster project-a-dev \
  --namespace kube-system \
  --name aws-load-balancer-controller \
  --role-name AmazonEKSLoadBalancerControllerRole \
  --attach-policy-arn $POLICY_ARN \
  --approve

# Spremi role ARN za Helm instalaciju
ALB_CONTROLLER_ROLE_ARN=$(aws iam get-role \
  --role-name AmazonEKSLoadBalancerControllerRole \
  --query 'Role.Arn' --output text)
```

**Šta je IRSA?** IAM Roles for Service Accounts. K8s pod (controller) može zvati AWS API bez ikakvih hardkodiranih AWS access key/secret. Radi preko federated identity: K8s SA token → AWS STS → temp credentials za IAM Role. Sigurniji i maintainable od alternatives.

---

## Korak 2: Instalacija ALB Controllera via Helm

```bash
# Dodaj EKS Helm repo
helm repo add eks https://aws.github.io/eks-charts
helm repo update

# Instaliraj controller
helm upgrade --install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=project-a-dev \
  --set serviceAccount.create=false \
  --set serviceAccount.name=aws-load-balancer-controller \
  --set serviceAccount.annotations."eks\.amazonaws\.com/role-arn"=$ALB_CONTROLLER_ROLE_ARN \
  --set region=eu-west-1 \
  --set vpcId=$(aws eks describe-cluster --name project-a-dev --query "cluster.resourcesVpcConfig.vpcId" --output text)

# Provjeri instalaciju
kubectl get deployment -n kube-system aws-load-balancer-controller
# READY 2/2 → OK

kubectl logs -n kube-system deployment/aws-load-balancer-controller --tail=20
# Treba vidjeti: "Starting controllers" bez ERROR logova
```

**Napomena:** `serviceAccount.create=false` jer smo SA već kreirali sa eksctl. Ako koristiš Terraform za IRSA, možeš pustiti Helm da kreira SA i samo proslijediš role ARN.

---

## Korak 3: Ingress Resource za project-a

```yaml
# ingress-project-a.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: project-a
  namespace: project-a-prod
  annotations:
    # Koji controller rukuje ovim Ingressom
    kubernetes.io/ingress.class: alb

    # ALB konfiguracija
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip          # direktno na pod IP, ne NodePort

    # SSL
    alb.ingress.kubernetes.io/certificate-arn: arn:aws:acm:eu-west-1:123456789:certificate/abc-def-123
    alb.ingress.kubernetes.io/ssl-redirect: "443"      # HTTP → HTTPS redirect na ALB nivou
    alb.ingress.kubernetes.io/listen-ports: '[{"HTTP":80},{"HTTPS":443}]'

    # Health checks
    alb.ingress.kubernetes.io/healthcheck-path: /health
    alb.ingress.kubernetes.io/healthcheck-interval-seconds: "15"
    alb.ingress.kubernetes.io/healthcheck-timeout-seconds: "5"
    alb.ingress.kubernetes.io/healthy-threshold-count: "2"
    alb.ingress.kubernetes.io/unhealthy-threshold-count: "2"
    alb.ingress.kubernetes.io/success-codes: "200"

    # Subneti (public!) — po imenu ili ID-u
    alb.ingress.kubernetes.io/subnets: subnet-aaa111,subnet-bbb222

    # Security group za ALB
    alb.ingress.kubernetes.io/security-groups: sg-alb-project-a-prod

    # Tagovi za cost tracking
    alb.ingress.kubernetes.io/tags: Environment=prod,Project=project-a
spec:
  rules:
    - host: app.firma.com
      http:
        paths:
          - path: /api
            pathType: Prefix
            backend:
              service:
                name: php-service
                port:
                  number: 9000
          - path: /
            pathType: Prefix
            backend:
              service:
                name: nginx-frontend
                port:
                  number: 80
```

```bash
kubectl apply -f ingress-project-a.yaml

# Prati kreiranje ALB-a (može potrajati 1-3 minute)
kubectl describe ingress project-a -n project-a-prod

# Kad je gotovo, ADDRESS polje ima ALB DNS:
# Address: project-a-prod-alb-789.eu-west-1.elb.amazonaws.com
```

**Redosled paths je bitan!** `/api` mora biti PRIJE `/` jer ALB primjenjuje pravila po redosledu. Ako `/` dođe prvo, uhvati sve — `/api` se nikad ne provjeri.

**`pathType: Prefix` vs `Exact`:**
- `Prefix /api` → matchuje `/api`, `/api/users`, `/api/v2/orders`
- `Exact /api` → matchuje samo `/api`, ne `/api/users`
- Za routing backend API-ja uvijek `Prefix`

---

## IngressGroup — Dijeli Jedan ALB

Ako imaš više Ingress resursa (app + monitoring + admin), bez IngressGroup svaki kreira poseban ALB. Sa IngressGroup dijele jedan ALB.

```yaml
# ingress-project-a.yaml (app traffic)
metadata:
  annotations:
    alb.ingress.kubernetes.io/group.name: project-a-prod  # isti group name
    alb.ingress.kubernetes.io/group.order: "10"           # redosled evaluacije pravila
    ...
spec:
  rules:
    - host: app.firma.com
      ...

---
# ingress-monitoring.yaml (Grafana/Prometheus)
metadata:
  annotations:
    alb.ingress.kubernetes.io/group.name: project-a-prod  # isti ALB!
    alb.ingress.kubernetes.io/group.order: "20"
    ...
spec:
  rules:
    - host: monitoring.firma.com
      ...
```

**Ušteda:** 2 ALB-a × $5.76/mj = $11.52/mj → 1 ALB = $5.76/mj. Na velikom clusteru sa 20 Ingress resursa, to je $115/mj razlike.

**Oprez:** Ako grupiraš Ingresse, scheme i security-groups annotation moraju biti konzistentni unutar grupe. Conflicting annotations → greška pri kreiranju.

---

## Napredne ALB Anotacije

```yaml
# WAF integracija (production must-have)
alb.ingress.kubernetes.io/wafv2-acl-arn: arn:aws:wafv2:eu-west-1:123:regional/webacl/project-a/xxx

# Access logs u S3
alb.ingress.kubernetes.io/load-balancer-attributes: |
  access_logs.s3.enabled=true,
  access_logs.s3.bucket=project-a-alb-logs,
  access_logs.s3.prefix=prod

# Connection draining — čekaj da aktivni requestovi završe pri deregistraciji
alb.ingress.kubernetes.io/target-group-attributes: |
  deregistration_delay.timeout_seconds=30

# Sticky sessions (session affinity) — svi requestovi od istog klijenta idu na isti pod
alb.ingress.kubernetes.io/target-group-attributes: |
  stickiness.enabled=true,
  stickiness.lb_cookie.duration_seconds=86400

# Custom response headers
alb.ingress.kubernetes.io/response-header-modifier: >
  [{"action":{"type":"AddHeader","header":{"name":"X-Content-Type-Options","value":"nosniff"}}}]
```

---

## Verifikacija i Debugging

```bash
# Status Ingressa i ALB DNS
kubectl get ingress -n project-a-prod
kubectl describe ingress project-a -n project-a-prod

# Events (tu vidiš greške ALB Controllera)
kubectl describe ingress project-a -n project-a-prod | grep -A 20 Events

# ALB Controller logovi — za dublje debuggovanje
kubectl logs -n kube-system deployment/aws-load-balancer-controller -f

# Provjeri da li K8s Services postoje i imaju endpoints
kubectl get svc -n project-a-prod
kubectl get endpoints php-service -n project-a-prod  # mora imati IP adrese

# Test routing direktno
kubectl run test --image=curlimages/curl -it --rm --restart=Never -- \
  curl -H "Host: app.firma.com" http://php-service.project-a-prod.svc.cluster.local:9000/health
```

**Česta greška: `Address` polje u Ingress je prazno nakon 5+ minuta**
- Provjeri ALB Controller logs: `kubectl logs -n kube-system deployment/aws-load-balancer-controller`
- Najčešće uzroci: IRSA nema prave permisije, subnet nije tagovan sa `kubernetes.io/role/elb=1`, security group ID ne postoji

**Subnet tagovi za ALB Controller:**
```
# Public subneti moraju imati tag:
kubernetes.io/role/elb = 1

# Private subneti (za internal ALB):
kubernetes.io/role/internal-elb = 1

# Oba tipa trebaju:
kubernetes.io/cluster/project-a-dev = shared  # ili "owned"
```

Bez ovih tagova, ALB Controller ne može pronaći subnetove i neće kreirati ALB.
