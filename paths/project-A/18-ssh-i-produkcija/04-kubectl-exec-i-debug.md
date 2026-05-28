# 04 — kubectl exec i Debug u Produkciji

## Pravila Prije Nego Što Otvoriš Terminal

`kubectl exec` u produkciji nije zabranjen, ali zahtijeva disciplinu. Razlika između iskusnog i neiskusnog inženjera: iskusan zna što ga košta svaka komanda.

### Obavezni ritual

```bash
# 1. Provjeri da si u pravom kontekstu (produkcija, ne dev!)
kubectl config current-context
# Očekivani output: prod (ili project-a-prod, ili sl.)

# 2. Provjeri u koji namespace ulaziš
kubectl get pods -n project-a-prod

# 3. Zabilježi akciju (Slack, incident ticket):
# "Ulazim u go-service-7d9f8c-xyz, debugiram MySQL timeout, ref: INC-456"
```

### Terminal session recording

Ako radiš nešto ozbiljno, snimi terminal sesiju:

```bash
# Počni snimanje (sve što vidiš u terminalu ide u fajl)
script -a ~/prod-debug-$(date +%Y%m%d-%H%M%S).log

# ... radi što trebaš ...

# Završi snimanje
exit

# Log fajl sada postoji kao dokaz
```

### Što smije, što ne smije

| Dozvoljeno (uz razlog) | Nikad u produkciji |
|------------------------|-------------------|
| `cat`, `ls`, `ps`, `top` | `rm`, `rmdir` |
| `grep` kroz logove | `chmod`, `chown` na app fajlove |
| `curl` za health check | `kill -9` bez razloga |
| `nslookup`, `ping`, `nc` | Schema migracije |
| `nginx -T` config provjera | `kubectl exec` pa `bash` skripte koje pišu |

---

## Korisne kubectl exec Komande za Project-A Servise

### PHP Service (php-fpm)

```bash
# Koji pod-ovi postoje?
kubectl get pods -n project-a-prod -l app=php-service

# Provjeri PHP-FPM procese
kubectl exec -it <php-pod> -n project-a-prod -- ps aux

# Provjeri PHP-FPM pool konfiguraciju
kubectl exec -it <php-pod> -n project-a-prod -- cat /usr/local/etc/php-fpm.d/www.conf

# Provjeri koliko PHP-FPM radnih procesa čeka vs obrađuje
kubectl exec -it <php-pod> -n project-a-prod -- \
  sh -c 'ps aux | grep php-fpm | grep -v grep | wc -l'

# PHP info (verzija, moduli)
kubectl exec -it <php-pod> -n project-a-prod -- php -v
kubectl exec -it <php-pod> -n project-a-prod -- php -m | grep -E 'pdo|mysql|redis'
```

### Go Service

```bash
# Provjeri otvorene konekcije prema MySQL (iz /proc/net/tcp)
# (hexadecimalni zapis — broj reda = broj konekcija)
kubectl exec -it <go-pod> -n project-a-prod -- \
  sh -c 'cat /proc/net/tcp | wc -l'

# Provjeri environment varijable (da li su secrets ispravno mountovani)
kubectl exec -it <go-pod> -n project-a-prod -- env | grep -E 'DB_|REDIS_|APP_'

# Da li Go servis "sluša" na očekivanom portu?
kubectl exec -it <go-pod> -n project-a-prod -- \
  sh -c 'cat /proc/net/tcp6 | grep 2710'
# 2710 hex = 10000 decimal — zamijeni sa tvojim portom

# Provjeri open file descriptors (za leak detection)
kubectl exec -it <go-pod> -n project-a-prod -- \
  sh -c 'ls /proc/1/fd | wc -l'
```

### Nginx

```bash
# Nginx config koji se stvarno koristi (kompletna konfiguracija)
kubectl exec -it <nginx-pod> -n project-a-prod -- nginx -T

# Test konfiguracije bez restarta
kubectl exec -it <nginx-pod> -n project-a-prod -- nginx -t

# Nginx status (ako je stub_status modul aktivan)
kubectl exec -it <nginx-pod> -n project-a-prod -- \
  curl -s localhost:8080/nginx_status

# Access log (zadnjih 50 linija)
kubectl exec -it <nginx-pod> -n project-a-prod -- \
  tail -50 /var/log/nginx/access.log
```

### DNS Resolution Debug

Čest izvor problema: servis ne može dosegnuti drugi servis po imenu.

```bash
# Provjeri DNS resolution iz Go pod-a prema MySQL servisu
kubectl exec -it <go-pod> -n project-a-prod -- \
  nslookup project-a-prod-mysql.project-a-prod.svc.cluster.local

# Format: <service-name>.<namespace>.svc.cluster.local

# Provjeri CoreDNS direktno
kubectl exec -it <go-pod> -n project-a-prod -- \
  nslookup project-a-prod-mysql.project-a-prod.svc.cluster.local 10.96.0.10
# 10.96.0.10 = uobičajena CoreDNS adresa (provjeri: kubectl get svc -n kube-system kube-dns)

# Provjeri /etc/resolv.conf unutar pod-a
kubectl exec -it <go-pod> -n project-a-prod -- cat /etc/resolv.conf

# Mrežna dostupnost (da li port odgovara)
kubectl exec -it <go-pod> -n project-a-prod -- \
  sh -c 'nc -zv project-a-prod-mysql.project-a-prod.svc.cluster.local 3306 && echo "OK" || echo "FAIL"'
```

---

## kubectl port-forward u Produkciji

`kubectl port-forward` preusmjerava promet sa tvoje lokalne mašine prema Kubernetes servisu ili podu — bez izlaganja resursa internetu.

### Grafana (Monitoring)

```bash
# Pristup Grafana lokalno bez expose na internet
kubectl port-forward svc/monitoring-grafana 3000:80 -n monitoring

# Sada otvori http://localhost:3000 u browseru
# Ctrl+C za prekid
```

### Redis Debug (Read-Only)

```bash
# Pristup Redis servisu lokalno
kubectl port-forward svc/redis 6379:6379 -n project-a-prod

# U drugom terminalu — read-only provjere:
redis-cli -h 127.0.0.1 -p 6379
> INFO server
> INFO stats
> DBSIZE
> TTL some-key

# NIKAD u produkciji: FLUSHALL, FLUSHDB, DEL masovne operacije
```

### MySQL (Samo za Read Debug)

```bash
# Port-forward na MySQL servis
kubectl port-forward svc/project-a-prod-mysql 3307:3306 -n project-a-prod

# U drugom terminalu
mysql -h 127.0.0.1 -P 3307 -u readonly_user -p

# Koristiti read-only korisnika — nikad root ili app user za debug
```

**Upozorenje:** port-forward drži otvorenu konekciju dok ne prekinete. Uvijek gasi kada završiš (`Ctrl+C`).

---

## Ephemeral Debug Containers (K8s 1.25+)

Scenarij: produkcijski pod nema `sh`, `bash`, `curl`, `nc` — distroless image ili minimal Alpine. Ephemeral debug container dodaje debug okruženje u **running pod bez restarting**:

```bash
# Dodaj busybox debug container u running pod
kubectl debug -it <pod-name> \
  --image=busybox \
  --target=go-service \
  -n project-a-prod

# Sada imaš busybox shell koji dijeli namespace sa go-service containerom

# Korisnije: netshoot image (bogat network debug alatkama)
kubectl debug -it <pod-name> \
  --image=nicolaka/netshoot \
  --target=go-service \
  -n project-a-prod

# U debug containeru:
# curl, wget, nslookup, dig, nc, tcpdump, ss, ip, iperf3...
```

Debug container se briše sam kad izađeš — ne ostaje u podu.

### Provjera Shared Process Namespace

Ako pod ima `shareProcessNamespace: true` u spec-u, iz debug containera možeš vidjeti sve procese:

```bash
# Iz netshoot debug containera
ps aux  # vidjet ćeš i Go servis procese

# Pratiti file system main containera
ls /proc/1/root/app/
```

---

## kubectl cp: Kopiranje Fajlova Iz Pod-a

```bash
# Kopiraj log fajl iz pod-a na lokalno
kubectl cp project-a-prod/<pod-name>:/app/logs/error.log ./prod-error.log

# Kopiraj core dump (ako Go servis crashira sa core dump)
kubectl cp project-a-prod/<pod-name>:/tmp/core ./core-dump-$(date +%Y%m%d)

# Format: <namespace>/<pod-name>:<path-inside-pod> <local-path>
```

Kopiranje iz pod-a je safe read operacija — ništa se ne mijenja u pod-u.

---

## Zajednički Antipaterni koje Treba Izbjegavati

### Antipattern 1: kubectl exec za rutinske operacije

```bash
# LOŠE — ovo se događa svaki dan
kubectl exec -it php-pod -- php artisan migrate

# DOBRO — migracije trebaju biti u CI/CD pipelinu kao Job
kubectl apply -f migrations-job.yaml
```

### Antipattern 2: Interaktivni bash u prod bez fokusa

```bash
# OPASNO — otvoren interaktivni shell, nema jasnog plana
kubectl exec -it go-pod -n project-a-prod -- bash

# BOLJE — specifična komanda sa jasnim ciljem
kubectl exec <go-pod> -n project-a-prod -- env | grep DB_HOST
```

### Antipattern 3: Copy-paste komandi bez razumijevanja

Nikad copy-pastovati komande iz interneta direktno u produkcijski pod. Pročitaj šta radi, razumij efekt.

---

## Kada kubectl exec Nije Dovoljan

Ako redovno trebaš `kubectl exec` za iste stvari, to je signal:

| Stalan razlog za exec | Pravi fix |
|----------------------|-----------|
| Gledam application logove | Centralizovani logging (Grafana Loki, ELK) |
| Treba mi query prema bazi | DB GUI + read replica + SSM port-forward |
| Provjeravam ENV varijable | `kubectl describe pod` bez exec-a |
| Restart aplikacije | `kubectl rollout restart deployment/...` |
| Provjera health endpoint-a | `kubectl get endpoints` + Prometheus probe |
