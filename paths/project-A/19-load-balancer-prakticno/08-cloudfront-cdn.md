# 08 — CloudFront CDN

**CloudFront CDN** — distribucija Vue.js statičkih fajlova globalno. Manji latency, manje opterećenje origin server-a, DDoS zaštita.

**Arhitektura sa CloudFront:**
```
Browser → CloudFront (edge location, 450+ lokacija) → Origin (ALB/S3)

Bez CDN:
  Browser (Beograd) → ALB (eu-west-1 Dublin) → ~40ms

Sa CDN:
  Browser (Beograd) → CloudFront Edge (Frankfurt) → ~8ms (cached)
```

**Terraform za CloudFront:**
```hcl
# terraform/modules/cloudfront/main.tf

# S3 bucket za Vue.js build artefakte
resource "aws_s3_bucket" "frontend" {
  bucket = "project-a-frontend-${var.env}-${var.account_id}"
}

resource "aws_s3_bucket_website_configuration" "frontend" {
  bucket = aws_s3_bucket.frontend.id
  index_document { suffix = "index.html" }
  error_document { key = "index.html" }   # SPA fallback
}

# CloudFront Origin Access Control (OAC) - modern pristup
resource "aws_cloudfront_origin_access_control" "main" {
  name                              = "project-a-${var.env}-oac"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

resource "aws_cloudfront_distribution" "main" {
  enabled             = true
  is_ipv6_enabled     = true
  default_root_object = "index.html"
  aliases             = [var.domain]   # app.firma.com

  # Vue.js static files iz S3
  origin {
    domain_name              = aws_s3_bucket.frontend.bucket_regional_domain_name
    origin_id                = "S3-frontend"
    origin_access_control_id = aws_cloudfront_origin_access_control.main.id
  }

  # API proxy → ALB (ne cache-uje API zahtjeve)
  origin {
    domain_name = var.alb_dns_name
    origin_id   = "ALB-api"
    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "https-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  # Default: serve Vue.js SPA iz S3
  default_cache_behavior {
    allowed_methods        = ["GET", "HEAD"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "S3-frontend"
    viewer_protocol_policy = "redirect-to-https"

    cache_policy_id            = aws_cloudfront_cache_policy.static.id
    response_headers_policy_id = aws_cloudfront_response_headers_policy.security.id

    compress = true   # Gzip/Brotli automatski
  }

  # /api/* → ALB (NE cache-uje)
  ordered_cache_behavior {
    path_pattern     = "/api/*"
    allowed_methods  = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "ALB-api"

    viewer_protocol_policy = "redirect-to-https"
    cache_policy_id        = data.aws_cloudfront_cache_policy.caching_disabled.id

    # Forwardi sve headere na ALB
    origin_request_policy_id = data.aws_cloudfront_origin_request_policy.all_viewer.id
  }

  # SPA fallback: sve nepoznate putanje → index.html
  custom_error_response {
    error_code            = 403
    response_code         = 200
    response_page_path    = "/index.html"
  }
  custom_error_response {
    error_code            = 404
    response_code         = 200
    response_page_path    = "/index.html"
  }

  # SSL sertifikat (us-east-1 obavezno za CloudFront!)
  viewer_certificate {
    acm_certificate_arn      = var.acm_certificate_arn_us_east_1  # Must be us-east-1!
    ssl_support_method       = "sni-only"
    minimum_protocol_version = "TLSv1.2_2021"
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  tags = {
    Environment = var.env
    Project     = "project-a"
  }
}

# Cache policy za statičke fajlove
resource "aws_cloudfront_cache_policy" "static" {
  name        = "project-a-static-${var.env}"
  min_ttl     = 0
  default_ttl = 86400     # 1 dan default
  max_ttl     = 31536000  # 1 godina max (za hashed fajlove)

  parameters_in_cache_key_and_forwarded_to_origin {
    cookies_config  { cookie_behavior = "none" }
    headers_config  { header_behavior = "none" }
    query_strings_config { query_string_behavior = "none" }
    enable_accept_encoding_gzip   = true
    enable_accept_encoding_brotli = true
  }
}

# Security headers policy
resource "aws_cloudfront_response_headers_policy" "security" {
  name = "project-a-security-headers-${var.env}"

  security_headers_config {
    strict_transport_security {
      access_control_max_age_sec = 31536000
      include_subdomains         = true
      preload                    = true
      override                   = true
    }
    content_type_options { override = true }
    frame_options {
      frame_option = "DENY"
      override     = true
    }
    referrer_policy {
      referrer_policy = "strict-origin-when-cross-origin"
      override        = true
    }
  }
}

# Data sources za AWS managed policies
data "aws_cloudfront_cache_policy" "caching_disabled" {
  name = "Managed-CachingDisabled"
}

data "aws_cloudfront_origin_request_policy" "all_viewer" {
  name = "Managed-AllViewer"
}

# S3 bucket policy: dozvoli samo CloudFront OAC pristup
resource "aws_s3_bucket_policy" "frontend" {
  bucket = aws_s3_bucket.frontend.id
  policy = data.aws_iam_policy_document.frontend_s3.json
}

data "aws_iam_policy_document" "frontend_s3" {
  statement {
    principals {
      type        = "Service"
      identifiers = ["cloudfront.amazonaws.com"]
    }
    actions   = ["s3:GetObject"]
    resources = ["${aws_s3_bucket.frontend.arn}/*"]
    condition {
      test     = "StringEquals"
      variable = "AWS:SourceArn"
      values   = [aws_cloudfront_distribution.main.arn]
    }
  }
}
```

**GitLab CI: deploy Vue.js na S3 + CloudFront invalidation:**
```yaml
deploy:frontend:cdn:
  stage: deploy
  image: amazon/aws-cli:latest
  needs: [build:vue]
  environment: production
  script:
    # Upload na S3
    - aws s3 sync services/frontend/dist/ s3://$FRONTEND_BUCKET/
        --delete
        --cache-control "max-age=31536000,immutable"
        --exclude "index.html"

    # index.html sa kratkim cache (nije immutable)
    - aws s3 cp services/frontend/dist/index.html s3://$FRONTEND_BUCKET/
        --cache-control "max-age=60,must-revalidate"

    # Invalidate CloudFront cache za index.html (sve ostalo je hashed)
    - aws cloudfront create-invalidation
        --distribution-id $CLOUDFRONT_DISTRIBUTION_ID
        --paths "/index.html" "/service-worker.js"
```

**Važna napomena za Vue.js build:**
```bash
# Vite hašira nazive fajlova: app.abc123.js (nikad ne mijenja URL)
# CloudFront može ih cacheovati godinu dana
# index.html se NIKAD ne hashira → kratki cache (60s)
```

**Cost CloudFront:**
```
CloudFront za ~100GB/mj saobraćaja:
  Data transfer:    $0.085/GB → ~$8.50
  HTTPS requests:   $0.01/10k → ~$1.00
  Total:            ~$10/mj

Bez CloudFront (ALB):
  ALB data:         $0.008/GB → ~$0.80
  ALB requests:     $0.008/LCU → varijabilno

CloudFront je JEFTINIJI za statičke fajlove + globalni audience.
```

**ACM Certificate napomena:**
```
CloudFront zahtijeva ACM sertifikat u us-east-1 (ne eu-west-1!)
Terraform: aws provider mora biti konfigurisan sa alias za us-east-1

provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"
}

resource "aws_acm_certificate" "cloudfront" {
  provider          = aws.us_east_1
  domain_name       = "*.firma.com"
  validation_method = "DNS"
}
```

**Variables:**
```hcl
variable "account_id" { type = string }
variable "acm_certificate_arn_us_east_1" { type = string }
variable "alb_dns_name" { type = string }
variable "domain" { type = string }
variable "env" { type = string }
```
