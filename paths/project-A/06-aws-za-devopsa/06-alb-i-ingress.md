# ALB i Kubernetes Ingress

## Zašto ALB, a ne NodePort ili NLB

Kubernetes Service tipa `NodePort` eksponira port direktno na worker nodovima. Ovo ne funkcioniše dobro za produkciju: treba javne IP adrese na nodovima, nema SSL termination, nema path-based routing.

**ALB (Application Load Balancer)** radi na Layer 7 (HTTP/HTTPS):
- SSL termination: HTTPS sertifikat je na ALB-u, backend prima HTTP
- Host-based routing: `app.firma.com` i `api.firma.com` → različiti servisi
- Path-based routing: `/api/` → jedan service, `/` → drugi
- Health check prema Podovima
- AWS WAF integracija (opciono)

**NLB (Network Load Balancer)** radi na Layer 4 (TCP/UDP):
- Nema SSL termination na aplikacijskom nivou
- Koristi se za non-HTTP protokole
- Nije za project-A

## AWS Load Balancer Controller

Kubernetes sam po sebi ne zna kako kreirati ALB. AWS Load Balancer Controller je Kubernetes operator koji čita Ingress resurse i kreira ALB-ove u AWS-u.

Instalira se kao Helm chart:
```bash
helm repo add eks https://aws.github.io/eks-charts
helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  --namespace kube-system \
  --set clusterName=project-a-dev \
  --set serviceAccount.annotations."eks\.amazonaws\.com/role-arn"=arn:aws:iam::123456:role/alb-controller
```

Controller koristi IRSA (IAM Role za ServiceAccount) za pristup AWS API-u — kreira i briše ALB, Target Group-e, Listeners.

## Ingress annotations za ALB

Kubernetes Ingress je API objekat koji definira HTTP routing. ALB Controller čita anotacije da konfigurira ALB:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: helloworld
  namespace: helloworld-dev
  annotations:
    kubernetes.io/ingress.class: alb
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
    alb.ingress.kubernetes.io/certificate-arn: arn:aws:acm:eu-west-1:123456789:certificate/abc-def
    alb.ingress.kubernetes.io/listen-ports: '[{"HTTPS":443},{"HTTP":80}]'
    alb.ingress.kubernetes.io/ssl-redirect: '443'
    alb.ingress.kubernetes.io/healthcheck-path: /
    alb.ingress.kubernetes.io/healthcheck-interval-seconds: '30'
spec:
  rules:
    - host: app.dev.firma.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: helloworld-service
                port:
                  number: 80
```

Ključne anotacije:
- `scheme: internet-facing` — ALB dobija javnu IP adresu (public subnet)
- `target-type: ip` — saobraćaj ide direktno na Pod IP, ne na node port
- `ssl-redirect: 443` — HTTP automatski redirectuje na HTTPS
- `certificate-arn` — ACM sertifikat za HTTPS

## SSL Termination na ALB

Tok HTTPS saobraćaja:
```
Klijent → HTTPS (443) → ALB (SSL termination, ACM cert) → HTTP (80) → Pod
```

ALB drži SSL sertifikat. Komunikacija između ALB-a i Pod-ova je HTTP unutar VPC private mreže. Ovo je sigurno jer je saobraćaj iznutar AWS mreže, ne izlazi na internet.

Ako je potreban end-to-end TLS (compliance zahtjev): ALB može prosljeđivati HTTPS na Pod koji isto terminira TLS. Kompleksnije, obično nije potrebno za project-A.

## Health check Target Group

ALB šalje HTTP GET na health check path svakog Pod-a. Ako Pod ne odgovori 200 OK, ALB ga izbacuje iz rotacije.

nginx servisaCi `index.html` → `GET /` vraća 200 → health check prolazi.

```
alb.ingress.kubernetes.io/healthcheck-path: /
alb.ingress.kubernetes.io/healthcheck-interval-seconds: '30'
alb.ingress.kubernetes.io/healthy-threshold-count: '2'
alb.ingress.kubernetes.io/unhealthy-threshold-count: '3'
```

## Veza sa project-A

Jedan ALB per environment, ne per aplikacija. Ako projekt dobije više servisa, IngressGroup anotacija dozvoljava dijeljenje jednog ALB-a:

```yaml
alb.ingress.kubernetes.io/group.name: dev-shared-alb
```

Svaki Ingress u istoj grupi dodaje pravila na isti ALB — ušteda $16/mj po servisu.

Terraform kreira Ingress kroz Helm values, ne direktno. Helm chart helloworld-a ima `ingress.enabled`, `ingress.host`, `ingress.certificateArn` kao values — environment-specific konfiguracija.
