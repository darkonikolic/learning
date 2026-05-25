# Unit 4 — Ingress: Edge Routing Overview

## Concept

An Ingress resource defines routing rules for external HTTP and HTTPS traffic into the cluster. An Ingress controller (nginx, Traefik, or a cloud provider's implementation) reads these rules and configures its proxy accordingly. TLS is terminated at the Ingress — the traffic between the Ingress controller and your services travels as plain HTTP inside the cluster. Path-based routing lets you direct `/api/v1` to one service and `/static` to another, all behind a single external IP address.

## Code

```yaml
# ingress.yaml — TLS termination + path-based routing
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: api-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - api.example.com
    secretName: api-tls-secret   # kubectl create secret tls api-tls-secret ...
  rules:
  - host: api.example.com
    http:
      paths:
      - path: /api/v1
        pathType: Prefix
        backend:
          service:
            name: api-service      # ClusterIP Service for the API
            port:
              number: 8080
      - path: /health
        pathType: Prefix
        backend:
          service:
            name: api-service
            port:
              number: 8080
---
# The backing Service (ClusterIP — internal only)
apiVersion: v1
kind: Service
metadata:
  name: api-service
spec:
  selector:
    app: api-server
  ports:
  - port: 8080
    targetPort: 8080
```

## Exercise

**Build:** Configure Ingress for your API service in a local cluster with the nginx Ingress controller.
**Input:** Your deployed API service with a ClusterIP Service.
**Output:** Ingress routing `/api/v1` to your service, accessible via `curl` through the Ingress IP.
**Acceptance:** (1) `curl http://<ingress-ip>/api/v1/products` returns 200. (2) Generate a self-signed cert and configure TLS — `curl -k https://api.example.com/api/v1/products` returns 200. (3) A path not listed in the rules (e.g., `/unknown`) returns 404 from the Ingress.

## Interview

- Where does TLS termination happen in this architecture? What are the security implications?
- What is the difference between a Service of type `ClusterIP`, `NodePort`, and `LoadBalancer`?
- Why do most clusters run only one Ingress controller even if they have many Ingress resources?
