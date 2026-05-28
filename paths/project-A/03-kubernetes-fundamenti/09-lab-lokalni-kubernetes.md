# 09 - LAB: Lokalni Kubernetes s kind

## Cilj

Na kraju ovog lab-a imat ćete:
- kind cluster s tri node-a koji radi lokalno
- hello-world nginx aplikaciju pokrenuti u Kubernetes-u
- Pristup kroz browser na `http://app.local`
- Razumijevanje toka: image → K8s manifest → running Pod

## Preduslovi

- Docker instaliran i pokrenut
- kubectl instaliran
- kind instaliran
- Završen LAB iz modula 02 (image u GitLab registryju)

## Korak 1: Instalacija kind i kubectl

```bash
# macOS
brew install kind kubectl

# Linux kind
curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64
chmod +x ./kind && sudo mv ./kind /usr/local/bin/kind

# Linux kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s \
  https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl && sudo mv kubectl /usr/local/bin/

# Provjera
kind version
kubectl version --client
docker version
```

## Korak 2: Kreiranje kind clustera

Sačuvajte kao `kind-config.yaml`:

```yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
  - role: control-plane
    kubeadmConfigPatches:
      - |
        kind: InitConfiguration
        nodeRegistration:
          kubeletExtraArgs:
            node-labels: "ingress-ready=true"
    extraPortMappings:
      - containerPort: 80
        hostPort: 80
        protocol: TCP
      - containerPort: 443
        hostPort: 443
        protocol: TCP
  - role: worker
  - role: worker
```

```bash
kind create cluster --name project-a --config kind-config.yaml

# Provjera
kubectl cluster-info --context kind-project-a
kubectl get nodes
# NAME                      STATUS   ROLES           AGE
# project-a-control-plane   Ready    control-plane   60s
# project-a-worker          Ready    <none>          45s
# project-a-worker2         Ready    <none>          45s
```

> **Podman:** Postavi provider prije kreiranja clustera:
> ```bash
> export KIND_EXPERIMENTAL_PROVIDER=podman
> kind create cluster --name project-a
> ```
> Napomena: Podman provider je eksperimentalan — preporučuje se Docker na Linuxu za kind.

## Korak 3: Instalacija nginx Ingress Controller-a

```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml

# Čekanje da bude spreman (može trajati 1-2 minute)
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=120s

echo "Ingress controller spreman"
```

## Korak 4: Kreiranje K8s manifesta

Kreirajte direktorij `k8s/` u vašem projektu sa sljedećim fajlovima:

**k8s/namespace.yaml:**
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: helloworld-dev
  labels:
    project: project-a
    environment: dev
```

**k8s/configmap.yaml:**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: nginx-config
  namespace: helloworld-dev
data:
  default.conf: |
    server {
        listen 80;
        server_name _;
        root /usr/share/nginx/html;
        index index.html;

        location / {
            try_files $uri $uri/ =404;
        }

        location /health {
            access_log off;
            return 200 "ok\n";
            add_header Content-Type text/plain;
        }
    }
```

**k8s/deployment.yaml:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: hello-world
  namespace: helloworld-dev
  labels:
    app: hello-world
    environment: dev
spec:
  replicas: 2
  selector:
    matchLabels:
      app: hello-world
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    metadata:
      labels:
        app: hello-world
        version: "latest"
    spec:
      containers:
        - name: nginx
          image: registry.gitlab.com/VAS-NAMESPACE/project-a:latest
          ports:
            - containerPort: 80
          resources:
            requests:
              cpu: "50m"
              memory: "64Mi"
            limits:
              cpu: "200m"
              memory: "128Mi"
          volumeMounts:
            - name: nginx-config
              mountPath: /etc/nginx/conf.d
              readOnly: true
          readinessProbe:
            httpGet:
              path: /health
              port: 80
            initialDelaySeconds: 5
            periodSeconds: 10
          livenessProbe:
            httpGet:
              path: /health
              port: 80
            initialDelaySeconds: 15
            periodSeconds: 20
      volumes:
        - name: nginx-config
          configMap:
            name: nginx-config
```

**k8s/service.yaml:**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: hello-world
  namespace: helloworld-dev
spec:
  selector:
    app: hello-world
  ports:
    - port: 80
      targetPort: 80
  type: ClusterIP
```

**k8s/ingress.yaml:**
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

## Korak 5: Konfiguracija pristupa GitLab registryju

Kind cluster treba credentials za povlačenje image-a iz privatnog registryja:

```bash
kubectl create secret docker-registry gitlab-registry-secret \
  --docker-server=registry.gitlab.com \
  --docker-username=VAS_GITLAB_USERNAME \
  --docker-password=VAS_PERSONAL_ACCESS_TOKEN \
  --docker-email=vas@email.com \
  -n helloworld-dev
```

Dodajte `imagePullSecrets` u deployment.yaml (u `spec.template.spec`):

```yaml
      imagePullSecrets:
        - name: gitlab-registry-secret
```

## Korak 6: Deploy na kind cluster

```bash
# /etc/hosts za lokalni DNS
echo "127.0.0.1 app.local" | sudo tee -a /etc/hosts

# Primjena svih manifesta
kubectl apply -f k8s/

# Praćenje deploymenta
kubectl get pods -n helloworld-dev --watch
# NAME                          READY   STATUS    RESTARTS   AGE
# hello-world-6d8b9c5f7-abc12   1/1     Running   0          30s
# hello-world-6d8b9c5f7-def34   1/1     Running   0          30s

# Provjera svih resursa
kubectl get all -n helloworld-dev
```

## Korak 7: Provjera u browseru

Otvorite browser: `http://app.local`

Trebali biste vidjeti "Hello World" stranicu.

CLI provjera:
```bash
curl http://app.local
# <!DOCTYPE html><html>...Hello World...

curl http://app.local/health
# ok
```

## Provjera stanja clustera

```bash
kubectl get all -n helloworld-dev

# Logovi
kubectl logs -l app=hello-world -n helloworld-dev

# Opisni detalji
kubectl describe deployment hello-world -n helloworld-dev

# Ulaz u kontejner
kubectl exec -it \
  $(kubectl get pod -l app=hello-world -n helloworld-dev -o jsonpath='{.items[0].metadata.name}') \
  -n helloworld-dev -- sh
```

## Korak 8: Simulacija rolling update-a

```bash
# Promijenite image tag
kubectl set image deployment/hello-world \
  nginx=registry.gitlab.com/VAS-NAMESPACE/project-a:novi-sha \
  -n helloworld-dev

# Pratite rolling update
kubectl rollout status deployment/hello-world -n helloworld-dev
# Waiting for deployment "hello-world" rollout to finish: 1 out of 2 new replicas updated...
# Waiting for deployment "hello-world" rollout to finish: 1 old replicas are pending termination...
# deployment "hello-world" successfully rolled out

# Rollback ako nešto pođe naopako
kubectl rollout undo deployment/hello-world -n helloworld-dev
```

## Brisanje clustera

```bash
# Brisanje svega u namespaceu
kubectl delete namespace helloworld-dev

# Brisanje cijelog clustera
kind delete cluster --name project-a

# Čišćenje /etc/hosts
sudo sed -i '' '/app.local/d' /etc/hosts
```

> **Podman:** `kind load docker-image <image> --name project-a` (isti, Podman build mora prethoditi)

## AI workflow: kind konfiguracija

Za napredne scenarije, pitajte Claude:

```
Trebam kind cluster koji simulira multi-zone setup s 3 worker node-a,
pritom svaki node u zasebnoj "zoni". Kako konfigurirati kind-config.yaml
i kako provjera da Podovi su raspoređeni na različite node-ove?
```

Ili:

```
Moj Pod je u ImagePullBackOff stanju. Evo kubectl describe outputa:

[paste output]

Koji je uzrok i kako riješiti?
```
