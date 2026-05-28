# 03 — Dockerfile: PHP servis

## Zašto Slim, ne Laravel

Laravel ima sjajan ekosistem ali nosi overhead koji ovaj servis ne koristi: Eloquent ORM (Go radi direktno sa MySQL-om), Blade templating (SPA nema potrebe), Auth sistem (PHP je samo proxy). Laravel image sa svim zavisnostima iznosi 400-500MB. Slim sa Composer zavisnostima: 80-120MB.

Slim je microframework — router + middleware pipeline + PSR-7. Ništa više. Upravo to nam treba za HTTP proxy servis.

---

## Multi-stage Dockerfile

```dockerfile
# ---- Composer/build stage ----
FROM composer:2.7 AS composer

WORKDIR /app

# Kopiraj samo composer fajlove za layer caching
COPY composer.json composer.lock ./

# Instaliraj samo production zavisnosti
# --no-dev: bez testing frameworka, debugbara i sl.
# --no-autoloader: autoloader generišemo zasebno sa optimizacijom
RUN composer install \
    --no-dev \
    --no-scripts \
    --no-autoloader \
    --prefer-dist

# Kopiraj source pa generiši optimizovani autoloader
COPY src/ src/
COPY public/ public/
RUN composer dump-autoload --optimize --no-dev

# ---- Runtime stage ----
FROM php:8.3-fpm-alpine

# Sistemske zavisnosti za PHP ekstenzije
RUN apk add --no-cache \
    libzip-dev \
    icu-dev \
    && docker-php-ext-install \
        zip \
        intl \
        opcache \
    # Redis ekstenzija (PECL, nije u core PHP)
    && apk add --no-cache --virtual .build-deps $PHPIZE_DEPS \
    && pecl install redis \
    && docker-php-ext-enable redis \
    && apk del .build-deps

# PHP production konfiguracija
COPY docker/php/php.ini /usr/local/etc/php/php.ini
COPY docker/php/www.conf /usr/local/etc/php-fpm.d/www.conf

WORKDIR /var/www/html

# Kopiraj artefakt iz composer stage-a
# --chown: PHP-FPM procesi rade kao www-data
COPY --from=composer --chown=www-data:www-data /app/vendor ./vendor
COPY --chown=www-data:www-data public/ ./public/
COPY --chown=www-data:www-data src/ ./src/

# Health check: provjeri da PHP-FPM odgovara
# cgi-fcgi je dostupan u php-fpm-alpine base image-u
HEALTHCHECK --interval=10s --timeout=5s --start-period=10s --retries=3 \
    CMD php -r "exit(0);" || exit 1

EXPOSE 9000

CMD ["php-fpm"]
```

---

## PHP-FPM konfiguracija za kontejner

```ini
; docker/php/www.conf
[www]
user = www-data
group = www-data

; Slušaj na TCP portu, ne Unix socket
; Unix socket je brži za isti host, ali nginx je u drugom kontejneru
listen = 0.0.0.0:9000

; Process manager: dynamic
; static: fiksni broj procesa — loše za container jer troši RAM čak i bez zahtjeva
; dynamic: skalira između pm.min i pm.max prema opterećenju — pravi izbor
; ondemand: spawn tek kada stigne zahtjev — loš latency pri hladnom startu
pm = dynamic
pm.max_children = 20
pm.start_servers = 5
pm.min_spare_servers = 2
pm.max_spare_servers = 8
pm.max_requests = 500  ; Restart worker-a svakih 500 zahtjeva — memory leak mitigacija

; Log na stdout/stderr — kontejner paradigma
; PHP-FPM logovi idu u Docker log driver
php_admin_value[error_log] = /proc/self/fd/2
php_admin_flag[log_errors] = on
```

`pm.max_requests = 500` je produkcijski pattern za PHP. PHP procesi mogu akumulirati memoriju kroz vijek rada (memory leaks u ekstenzijama ili aplikacijskom kodu). Restart svakih 500 zahtjeva je preventivna mjera, ne zakrpa za bugove.

---

## php.ini za produkciju

```ini
; docker/php/php.ini

[PHP]
; Memorija po procesu — proxy servis, ne treba previše
memory_limit = 128M

; Timeout za izvršavanje skripte
max_execution_time = 30

; Upload limitovi (ako PHP prima file upload-e)
upload_max_filesize = 10M
post_max_size = 10M

; Sakrij PHP verziju iz HTTP headera — security through obscurity
expose_php = Off

[opcache]
; Opcache je obavezan u produkciji — bez njega PHP parsira PHP fajlove na svaki zahtjev
opcache.enable = 1
opcache.memory_consumption = 128
opcache.interned_strings_buffer = 8
opcache.max_accelerated_files = 4000

; U kontejneru: timestampovi se ne mijenjaju (image je immutable)
; Revalidation provjera je nepotreban overhead — isključiti
opcache.revalidate_freq = 0
opcache.validate_timestamps = 0

; JIT (PHP 8.x): za CPU-bound operacije može dati 10-20% boost
; Za I/O-bound proxy servis: zanemarljiv benefit, može se ostaviti isključen
; opcache.jit_buffer_size = 100M
; opcache.jit = 1255

[Session]
; Session storage: Redis (ne filesystem)
session.save_handler = redis
session.save_path = "tcp://redis:6379?auth=${REDIS_PASSWORD}"
session.gc_maxlifetime = 86400  ; 24 sata
session.cookie_httponly = 1     ; JavaScript ne može čitati session cookie
session.cookie_secure = 1       ; Samo HTTPS (u produkciji)
session.cookie_samesite = Strict
```

`validate_timestamps = 0` je kritično u Docker kontejneru. Opcache inače provjerava je li fajl na disku noviji od keširane verzije. U immutable kontejneru, fajlovi se nikad ne mijenjaju — ova provjera je čist overhead.

---

## Health check endpoint

`/health` endpoint u Slim-u koji provjera zavisnosti:

```php
<?php
// src/routes.php ili u bootstrap-u

$app->get('/health', function ($request, $response) {
    $checks = [];
    $healthy = true;

    // Provjeri Redis konekciju
    try {
        $redis = new Redis();
        $redis->connect(getenv('REDIS_HOST'), 6379);
        $redis->ping();
        $checks['redis'] = 'ok';
    } catch (Exception $e) {
        $checks['redis'] = 'failed: ' . $e->getMessage();
        $healthy = false;
    }

    // Provjeri Go service dostupnost
    $goHealth = @file_get_contents('http://go-service:8080/health');
    if ($goHealth === false) {
        $checks['go-service'] = 'failed';
        $healthy = false;
    } else {
        $checks['go-service'] = 'ok';
    }

    $status = $healthy ? 200 : 503;
    $response->getBody()->write(json_encode([
        'status' => $healthy ? 'healthy' : 'degraded',
        'checks' => $checks,
        'timestamp' => time(),
    ]));

    return $response
        ->withStatus($status)
        ->withHeader('Content-Type', 'application/json');
});
```

Health check koji samo vraća `200 OK` bez provjere zavisnosti je nekoristan za K8s readiness probe — K8s misli da je servis spreman, a Redis konekcija možda nije uspostavljena. Pravi health check testira sve što servis treba da bi funkcionisao.

---

## Slim middleware za rate limiting i request proxying

```php
<?php
// src/Middleware/RateLimitMiddleware.php

class RateLimitMiddleware {
    private Redis $redis;
    private int $maxRequests;
    private int $windowSeconds;

    public function __construct(Redis $redis, int $maxRequests = 60, int $windowSeconds = 60) {
        $this->redis = $redis;
        $this->maxRequests = $maxRequests;
        $this->windowSeconds = $windowSeconds;
    }

    public function __invoke(Request $request, RequestHandler $handler): Response {
        $key = 'rate:' . ($request->getAttribute('user_id') ?? $request->getServerParams()['REMOTE_ADDR']);

        // Sliding window counter u Redis-u
        $current = $this->redis->incr($key);
        if ($current === 1) {
            $this->redis->expire($key, $this->windowSeconds);
        }

        if ($current > $this->maxRequests) {
            $response = new \Slim\Psr7\Response();
            $response->getBody()->write(json_encode(['error' => 'Rate limit exceeded']));
            return $response->withStatus(429)->withHeader('Content-Type', 'application/json');
        }

        return $handler->handle($request);
    }
}
```

Rate limiting u PHP middleware-u znači da Go servis nikad ne vidi prekomjerne zahtjeve. Alternativa (rate limit u Go-u) duplicira logiku i zahtijeva da svaki Go endpoint implementira provjeru.
