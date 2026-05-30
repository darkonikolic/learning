# 03 - Ingress i Networking

## Zašto Ingress

Bez Ingress-a, svaki Service koji trebate izložiti prema van dobija vlastiti LoadBalancer. Na AWS-u to znači poseban ELB po servisu — skupo i teško za upravljanje. Na lokalnom clusteru nema LoadBalancer tipa bez dodatnih alata.

**Ingress** je Kubernetes resurs koji definuje HTTP/HTTPS routing pravila: koji zahtjev ide na koji Service. Jedan ulazni load balancer → mnogo servisa, rutiranje po hostu ili putanji.

```
Internet
    ↓
LoadBalancer (jedan!)
    ↓
Ingress Controller (nginx, traefik...)
    ↓
Ingress resource (pravila)
    ↓
Services → Pods
```

## Ingress Controller vs Ingress Resource

Ovo je česta konfuzija:

**Ingress Controller** — stvarni program koji čita Ingress resurse i implementira routing. Nginx Ingress Controller, Traefik, AWS ALB Ingress Controller... Mora biti instaliran zasebno (nije ugrađen u Kubernetes).

**Ingress Resource** — Kubernetes YAML koji definiše pravila. Samo deklaracija, nema smisla bez controller-a.

Za project-A lokalno: **nginx ingress controller**. Na AWS EKS-u: **AWS Load Balancer Controller** koji kreira ALB.

Instalacija nginx ingress controllera za kind:

```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml

# Pričekajte da bude spreman
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=90s
```

## Ingress Resource: routing po hostu i putanji

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: hello-world
  namespace: helloworld-dev
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  ingressClassName: nginx
  rules:
    - host: app.local                    # po hostu
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: hello-world
                port:
                  number: 80
```

Routing po putanji (više servisa na istom hostu):

```yaml
spec:
  rules:
    - host: project-a.local
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: hello-world
                port:
                  number: 80
          - path: /api
            pathType: Prefix
            backend:
              service:
                name: api-service
                port:
                  number: 3000
          - path: /metrics
            pathType: Prefix
            backend:
              service:
                name: prometheus
                port:
                  number: 9090
```

## TLS u Ingressu — nije opcija

> **TLS blok je obavezan u svakom Ingress resursu od prvog puta.** Lokalno koristiš self-signed Secret, na AWS-u ACM certifikat kroz Ingress annotation. Ingress bez TLS bloka je privremeno rješenje koje se zaboravi ukloniti.

Kreiranje TLS Secret-a iz lokalnih certifikata (generirani s `make cert-local-mkcert` ili `make cert-local-openssl`):

```bash
# Kreiraj K8s TLS secret iz lokalnih certifikata
kubectl create secret tls app-tls-secret \
  --cert=certs/app.local.crt \
  --key=certs/app.local.key \
  -n dev
```

Ili koristeći Makefile target koji radi dry-run + apply:

```bash
NS=dev make cert-k8s-secret
```

Kompletan Ingress sa TLS — ovako izgleda svaki Ingress u project-A pathu:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: app-ingress
  namespace: dev
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  ingressClassName: nginx
  tls:
    - hosts:
        - app.local
      secretName: app-tls-secret
  rules:
    - host: app.local
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: app-svc
                port:
                  number: 8080
```

`ssl-redirect: "true"` annotation govori nginx ingress controlleru da automatski radi HTTP → HTTPS redirect — ekvivalent `return 301` u lokalnom nginx.conf.

Stariji primjer (samo za referencu, ako ga vidiš u kodu — dodaj TLS blok):

```yaml
# OVAJ OBLIK DOPUNI TLS BLOKOM
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: hello-world
  namespace: helloworld-dev
spec:
  ingressClassName: nginx
  tls:
    - hosts:
        - app.local
      secretName: hello-world-tls
  rules:
    - host: app.local
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: hello-world
                port:
                  number: 80
```

## Kind lokalno: /etc/hosts za simulaciju domena

Kind cluster nema pravi DNS. Da bi `app.local` radilo u browseru, dodajte u `/etc/hosts`:

```bash
# macOS/Linux
echo "127.0.0.1 app.local" | sudo tee -a /etc/hosts

# Provjera
ping app.local
```

Zašto `127.0.0.1`? Kind config je prosledio port 80 s localhost-a u cluster (extraPortMappings iz prethodnog fajla). Nginx ingress controller sluša na tom portu.

Pristup: `http://app.local` ili `https://app.local` (browser će upozoriti na self-signed cert — uredu je za lokalni razvoj).

## AWS: AWS Load Balancer Controller

Na EKS-u, Ingress s `ingressClassName: alb` kreira pravi AWS Application Load Balancer:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: hello-world
  namespace: helloworld-dev
  annotations:
    kubernetes.io/ingress.class: alb
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
    alb.ingress.kubernetes.io/certificate-arn: arn:aws:acm:region:id:certificate/xxx
    alb.ingress.kubernetes.io/ssl-redirect: "443"
spec:
  ingressClassName: alb
  rules:
    - host: dev.project-a.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: hello-world
                port:
                  number: 80
```

ACM certifikat se referencira ARN-om. AWS kontroler automatski kreira/ažurira ALB — nema ručne konfiguracije load balancera.

## Veza sa project-A: lokalni vs cloud flow

```
LOKALNO (kind):
Browser → localhost:80 → kind extraPortMappings
  → nginx ingress controller
  → hello-world Service
  → nginx Pod
  (TLS: self-signed cert u K8s Secret)

AWS EKS:
Browser → Route53 DNS → ALB (ACM cert, TLS termination)
  → AWS Load Balancer Controller
  → hello-world Service
  → nginx Pod
```

Kubernetes manifesti su isti (Deployment, Service). Jedino Ingress se razlikuje po ingressClassName i AWS-specifičnim anotacijama. U kasnijim modulima ćemo koristiti Kustomize overlays da upravljamo ovim razlikama.
