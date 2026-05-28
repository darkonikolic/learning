# 07 — cert-manager i interni TLS (PHP → Go mTLS unutar Kubernetesa)

## Kontekst

PHP 8.3 service poziva Go 1.22 service unutar Kubernetes clustera. Trenutno: plain HTTP. Cilj: TLS za PHP → Go komunikaciju koristeći cert-manager.

---

## Zašto cert-manager

- **Jedan alat za sve certifikate**: Let's Encrypt (public/Ingress TLS), interni CA (service-to-service), custom CA za testna okruženja
- **Automatsko obnavljanje** — cert-manager prati expiry i obnavlja certifikate transparentno, nema ručnog upravljanja
- **Kubernetes-nativni CRD-ovi**: `Certificate`, `Issuer`, `ClusterIssuer`, `CertificateRequest`, `CertificateSigningRequest`
- **Decoupling od infrastrukture** — isti manifest radi lokalno (self-signed), na stagging-u i produkciji (Let's Encrypt ili privatni PKI)

---

## Instalacija cert-manager

```bash
helm repo add jetstack https://charts.jetstack.io
helm repo update

helm upgrade --install cert-manager jetstack/cert-manager \
  --namespace cert-manager \
  --create-namespace \
  --set installCRDs=true \
  --version v1.14.0
```

`installCRDs=true` — bez ovoga cert-manager nema CRD-ove i odmah pada. U produkciji možeš CRD-ove instalirati odvojeno (`kubectl apply -f crds.yaml`) za bolju kontrolu pri upgradeu.

Verifikacija:
```bash
kubectl get pods -n cert-manager
# Trebas vidjeti: cert-manager, cert-manager-cainjector, cert-manager-webhook — sve Running
```

---

## Bootstrap: interni CA u tri koraka

Lanac povjerenja: `selfsigned-issuer` (nema CA, samo potpisuje sam sebe) → root CA certifikat → `project-a-internal-ca-issuer` (koristi root CA za potpisivanje servisnih certifikata).

```yaml
# Korak 1: Self-signed issuer — bootstrap alat, nema nikakvu vanjsku zavisnost.
# Jedina mu je svrha da potpiše root CA cert u koraku 2.
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: selfsigned-issuer
spec:
  selfSigned: {}

---
# Korak 2: Root CA certifikat za project-a interni PKI.
# isCA: true → cert ima KeyUsage: CertSign, može potpisivati druge certe.
# secretName: cert-manager sprema ca.crt + tls.crt + tls.key u ovaj Secret.
# ECDSA P-256: brži od RSA 2048 za TLS handshake, jednako siguran.
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: project-a-internal-ca
  namespace: cert-manager
spec:
  isCA: true
  commonName: project-a-internal-ca
  secretName: project-a-internal-ca-secret
  privateKey:
    algorithm: ECDSA
    size: 256
  issuerRef:
    name: selfsigned-issuer
    kind: ClusterIssuer

---
# Korak 3: CA-based ClusterIssuer — svi interni servisi koriste ovaj issuer.
# ClusterIssuer (ne Issuer) → dostupan u svim namespacima, ne treba replicati po namespaceima.
# secretName mora biti u namespace-u cert-manager (gdje ClusterIssuer živi).
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: project-a-internal-ca-issuer
spec:
  ca:
    secretName: project-a-internal-ca-secret
```

Primijeni jednom, globalno za cijeli cluster:
```bash
kubectl apply -f internal-ca.yaml
kubectl get clusterissuer  # STATUS: True = spreman
```

---

## Certificate za Go service

```yaml
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: go-service-tls
  namespace: project-a-prod
spec:
  # cert-manager kreira ovaj K8s Secret automatski i drži ga ažurnim.
  # Secret sadrži: tls.crt (chain), tls.key, ca.crt
  secretName: go-service-tls-secret

  # 90 dana trajanje — dovoljno dugo da ne troši resurse, kratko za sigurnost
  duration: 2160h

  # Obnovi 15 dana prije isteka — daje dovoljno vremena da se propagira
  renewBefore: 360h

  commonName: go-service.project-a-prod.svc.cluster.local

  # SAN (Subject Alternative Names) — TLS validacija gleda SAN, ne commonName!
  # Svaki DNS oblik kojim PHP može pozvati Go servis mora biti ovdje.
  dnsNames:
    - go-service                                          # kratki naziv (isti namespace)
    - go-service.project-a-prod                          # cross-namespace kratki
    - go-service.project-a-prod.svc                      # FQDN bez cluster domene
    - go-service.project-a-prod.svc.cluster.local        # puni FQDN
  issuerRef:
    name: project-a-internal-ca-issuer
    kind: ClusterIssuer
```

---

## Go service: TLS server

Secret `go-service-tls-secret` montiran je kao volume u pod. cert-manager automatski ažurira Secret — Go servis mora pratiti promjene certifikata (ili se restartati, što Kubernetes radi ako koristiš `cert-manager.io/inject-restart: "true"` anotaciju na Deploymentu).

```go
// cmd/server/main.go
package main

import (
    "crypto/tls"
    "log"
    "net/http"
)

func main() {
    // Certifikat i ključ montirani iz go-service-tls-secret volumena.
    // tls.LoadX509KeyPair čita PEM fajlove s diska.
    cert, err := tls.LoadX509KeyPair(
        "/etc/tls/tls.crt",
        "/etc/tls/tls.key",
    )
    if err != nil {
        log.Fatalf("failed to load TLS cert: %v", err)
    }

    server := &http.Server{
        Addr:    ":8443",
        Handler: setupRoutes(),
        TLSConfig: &tls.Config{
            Certificates: []tls.Certificate{cert},
            // TLS 1.3 jedina opcija — nema legacy ranjivosti (BEAST, POODLE, ROBOT...)
            MinVersion: tls.VersionTLS13,
        },
    }

    log.Println("Go service listening on :8443 (TLS)")
    // Prazni stringovi → koristi cert iz TLSConfig (već učitan iznad)
    log.Fatal(server.ListenAndServeTLS("", ""))
}
```

Za produkciju dodaj watcher koji detektuje promjenu certifikata i reload-a bez downtimea — `fsnotify` na `/etc/tls/tls.crt`.

---

## Go Deployment: volume mount

```yaml
spec:
  template:
    metadata:
      # cert-manager može triggerat rolling restart pri obnavljanju certa
      annotations:
        cert-manager.io/inject-restart: "true"
    spec:
      volumes:
        # Izvor: Secret koji cert-manager kreira i ažurira
        - name: tls-cert
          secret:
            secretName: go-service-tls-secret
            # defaultMode: 0400 — certifikati nisu world-readable
            defaultMode: 0400

      containers:
        - name: go-service
          image: registry.example.com/project-a/go-service:latest
          volumeMounts:
            - name: tls-cert
              mountPath: /etc/tls
              readOnly: true
          ports:
            - containerPort: 8443
              name: https
          # Liveness/readiness probe mora koristiti HTTPS
          livenessProbe:
            httpGet:
              path: /healthz
              port: 8443
              scheme: HTTPS
```

---

## PHP service: HTTPS klijent sa CA verifikacijom

```php
<?php
// src/Infrastructure/Http/GoServiceClient.php

use GuzzleHttp\Client;
use GuzzleHttp\Exception\RequestException;

class GoServiceClient
{
    private Client $client;

    public function __construct()
    {
        $this->client = new Client([
            'base_uri' => 'https://go-service:8443',

            // Putanja do CA certifikata montiranog iz project-a-internal-ca-secret.
            // Guzzle verifikuje da je Go servisov cert potpisan od strane ovog CA.
            'verify'   => '/etc/internal-ca/ca.crt',

            'timeout'  => 5.0,

            // Connection timeout odvojen od read timeout-a
            'connect_timeout' => 2.0,
        ]);
    }

    public function get(string $path): array
    {
        try {
            $response = $this->client->get($path);
            return json_decode($response->getBody()->getContents(), true);
        } catch (RequestException $e) {
            throw new \RuntimeException(
                'Go service call failed: ' . $e->getMessage(),
                $e->getCode(),
                $e
            );
        }
    }
}

// NIKAD: 'verify' => false
// Bez verifikacije TLS ne pruža zaštitu od MITM napada unutar clustera.
// Napadač koji kompromituje jedan pod može interceptovati sav promet.
```

---

## PHP Deployment: CA cert volume

```yaml
spec:
  template:
    spec:
      volumes:
        # project-a-internal-ca-secret sadrži: ca.crt, tls.crt, tls.key
        # PHP-u treba SAMO ca.crt za verifikaciju — ne treba privatni ključ!
        - name: internal-ca
          secret:
            secretName: project-a-internal-ca-secret
            items:
              - key: ca.crt      # samo javni CA cert
                path: ca.crt

      containers:
        - name: php-service
          volumeMounts:
            - name: internal-ca
              mountPath: /etc/internal-ca
              readOnly: true
```

Minimalni pristup: PHP pod ne dobija Go-servisov privatni ključ, ne dobija cijeli CA Secret — dobija samo `ca.crt`. Principle of least privilege.

---

## Service za Go (HTTPS port)

```yaml
apiVersion: v1
kind: Service
metadata:
  name: go-service
  namespace: project-a-prod
spec:
  selector:
    app: go-service
  ports:
    - name: https
      port: 8443
      targetPort: 8443
      protocol: TCP
  # Ne koristiti port 80/HTTP — nema fallback na plaintext
```

---

## Monitoring certifikata

cert-manager eksportuje Prometheus metrike automatski (port 9402 na cert-manager podu):

```yaml
# Ključne metrike:
# certmanager_certificate_expiration_timestamp_seconds — unix timestamp expiry
# certmanager_certificate_ready_status — 1 = OK, 0 = problem

# PrometheusRule — alarm 7 dana prije isteka:
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: cert-expiry-alerts
  namespace: cert-manager
spec:
  groups:
    - name: cert-manager
      rules:
        - alert: CertificateExpiringIn7Days
          expr: |
            certmanager_certificate_expiration_timestamp_seconds
            - time() < 7 * 24 * 3600
          for: 1h
          labels:
            severity: warning
          annotations:
            summary: "Certificate {{ $labels.name }} ističe za manje od 7 dana"
            description: "Namespace: {{ $labels.namespace }}"
```

Provjera statusa ručno:
```bash
kubectl get certificate -n project-a-prod
# READY: True = certifikat validan i ažuran

kubectl describe certificate go-service-tls -n project-a-prod
# Events: sekcija pokazuje svaki renewal pokušaj
```

---

## Helm integracija

```yaml
# helm/project-a/values.yaml
certManager:
  enabled: true
  issuerRef:
    name: project-a-internal-ca-issuer
    kind: ClusterIssuer
  certificate:
    duration: 2160h
    renewBefore: 360h
```

```yaml
# helm/project-a/templates/go-service-certificate.yaml
{{- if .Values.certManager.enabled }}
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: go-service-tls
  namespace: {{ .Release.Namespace }}
spec:
  secretName: go-service-tls-secret
  duration: {{ .Values.certManager.certificate.duration }}
  renewBefore: {{ .Values.certManager.certificate.renewBefore }}
  commonName: go-service.{{ .Release.Namespace }}.svc.cluster.local
  dnsNames:
    - go-service
    - go-service.{{ .Release.Namespace }}
    - go-service.{{ .Release.Namespace }}.svc
    - go-service.{{ .Release.Namespace }}.svc.cluster.local
  issuerRef:
    name: {{ .Values.certManager.issuerRef.name }}
    kind: {{ .Values.certManager.issuerRef.kind }}
{{- end }}
```

---

## Napomena o service mesh (Istio / Linkerd)

Ovaj pristup (cert-manager + eksplicitni TLS) je **preporučen za project-a** iz nekoliko razloga:

| | cert-manager (ovaj pristup) | Istio / Linkerd |
|---|---|---|
| Vidljivost | Vidiš svaki certifikat u K8s | mTLS je transparentan, teže debugirati |
| Kompleksnost | Umjerena — samo cert-manager | Visoka — cijeli service mesh control plane |
| Code promjene | Go: port 8443 + TLS config | Nula — sidecar proxy radi sve |
| Produkcija > 5 servisa | Postaje verbose | Svrsishodan |

Za projekt sa 2-3 servisa: cert-manager je pravo rješenje. Za 10+ servisa: Istio/Linkerd ima smisla — ali uvodi značajnu operativnu kompleksnost.
