# 05 — gRPC u Kubernetes

## K8s Service za gRPC

```yaml
# services/go-notification-service/k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: go-notification-service
  namespace: project-a-prod
  annotations:
    # NLB za gRPC ako ikad expose-uješ van clustera (ne ALB!)
    service.beta.kubernetes.io/aws-load-balancer-type: "nlb"
spec:
  selector:
    app: go-notification-service
  ports:
    - name: grpc
      port: 50051
      targetPort: 50051
      protocol: TCP
  type: ClusterIP   # Interno, ne expose van clustera
```

`ClusterIP` znači da je servis dostupan samo unutar K8s clustera.
DNS: `go-notification-service.project-a-prod.svc.cluster.local:50051`
Kratka forma unutar istog namespacea: `go-notification-service:50051`

## Deployment

```yaml
# services/go-notification-service/k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: go-notification-service
  namespace: project-a-prod
  labels:
    app: go-notification-service
spec:
  replicas: 2
  selector:
    matchLabels:
      app: go-notification-service
  template:
    metadata:
      labels:
        app: go-notification-service
    spec:
      containers:
        - name: notification
          image: registry.gitlab.com/youruser/project-a/go-notification-service:v1.0
          ports:
            - containerPort: 50051
              name: grpc
          env:
            - name: GRPC_PORT
              value: "50051"
            - name: SMTP_HOST
              valueFrom:
                secretKeyRef:
                  name: ses-credentials
                  key: smtp_host
            - name: SMTP_PORT
              valueFrom:
                secretKeyRef:
                  name: ses-credentials
                  key: smtp_port
            - name: SMTP_FROM
              valueFrom:
                secretKeyRef:
                  name: ses-credentials
                  key: smtp_from
            - name: SMTP_USERNAME
              valueFrom:
                secretKeyRef:
                  name: ses-credentials
                  key: smtp_username
            - name: SMTP_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: ses-credentials
                  key: smtp_password
          # K8s 1.24+ native gRPC health check (bez custom HTTP endpoint-a)
          readinessProbe:
            grpc:
              port: 50051
            initialDelaySeconds: 5
            periodSeconds: 10
            failureThreshold: 3
          livenessProbe:
            grpc:
              port: 50051
            initialDelaySeconds: 15
            periodSeconds: 30
            failureThreshold: 3
          resources:
            requests:
              cpu: 50m
              memory: 64Mi
            limits:
              cpu: 200m
              memory: 128Mi
```

## Zašto NLB za gRPC (ako ikad expose-uješ prema van)

| Load Balancer | Layer | HTTP/2 | gRPC Streaming |
|---------------|-------|--------|----------------|
| ALB (Application) | 7 | Terminira HTTP/2 | NE radi — pretvara u HTTP/1.1 |
| NLB (Network) | 4 | Prosleđuje TCP | Da — gRPC radi nativno |

Za interno (`ClusterIP`): nema LB-a, K8s DNS rutira direktno na pod.
Za external access: NLB → target group → node port → pod.

## TLS za gRPC via cert-manager

Za internu komunikaciju unutar clustera TLS nije obavezan (mTLS via Istio/Linkerd
je bolji izbor za zero-trust). Ako ipak trebaš TLS:

```yaml
# cert-manager Certificate za notification service
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: notification-service-tls
  namespace: project-a-prod
spec:
  secretName: notification-service-tls-secret
  dnsNames:
    - go-notification-service
    - go-notification-service.project-a-prod.svc.cluster.local
  issuerRef:
    name: project-a-internal-ca-issuer
    kind: ClusterIssuer
```

```go
// Server: učitaj TLS cert iz mounted secreta
creds, err := credentials.NewServerTLSFromFile(
    "/etc/tls/tls.crt",
    "/etc/tls/tls.key",
)
grpcServer := grpc.NewServer(grpc.Creds(creds))

// Klijent: učitaj CA cert
creds, err := credentials.NewClientTLSFromFile("/etc/tls/ca.crt", "")
conn, err := grpc.Dial(target, grpc.WithTransportCredentials(creds))
```

## HorizontalPodAutoscaler za notification service

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: go-notification-service
  namespace: project-a-prod
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: go-notification-service
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
```

## Environment variable za go-service

go-service treba znati adresu notification servisa:

```yaml
# U go-service deployment.yaml:
env:
  - name: NOTIFICATION_SERVICE_ADDR
    value: "go-notification-service:50051"
  # ili pun DNS:
  # value: "go-notification-service.project-a-prod.svc.cluster.local:50051"
```

## Debuggovanje u K8s

```bash
# Port forward pa grpcurl lokalno
kubectl port-forward svc/go-notification-service 50051:50051 -n project-a-prod

grpcurl -plaintext localhost:50051 list
grpcurl -plaintext \
  -d '{"to":"test@test.com","token":"abc","base_url":"http://localhost","user_id":1}' \
  localhost:50051 \
  notification.v1.NotificationService/SendVerificationEmail

# Ili exec u go-service pod (ako ima grpcurl binarni)
kubectl exec -it deploy/go-service -n project-a-prod -- \
  grpcurl -plaintext go-notification-service:50051 grpc.health.v1.Health/Check

# Logs notification service-a
kubectl logs -l app=go-notification-service -n project-a-prod --tail=100 -f
```
