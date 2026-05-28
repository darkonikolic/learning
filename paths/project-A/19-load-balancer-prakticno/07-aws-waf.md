# 07 — AWS WAF

**AWS WAF** — Web Application Firewall. Blokira maliciozni saobraćaj na ALB nivou.

**Šta WAF može:**
- SQL injection detekcija i blokiranje
- XSS detekcija
- Rate limiting po IP (AWS Managed Rules)
- Geo-blocking (zabrani pristup iz određenih zemalja)
- IP reputation lists (botovi, TOR, proxy-ji)
- Custom pravila za specifične napade

**Terraform za WAF:**
```hcl
# terraform/modules/waf/main.tf

resource "aws_wafv2_web_acl" "main" {
  name  = "project-a-${var.env}"
  scope = "REGIONAL"    # Za ALB (ne CloudFront)

  default_action {
    allow {}    # Default: propusti sve (whitelist approach)
  }

  # ── AWS Managed Rules (preporučeno, bez konfiguracije) ──────────

  # Core Rule Set: SQL injection, XSS, command injection
  rule {
    name     = "AWSManagedRulesCommonRuleSet"
    priority = 1

    override_action { none {} }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesCommonRuleSet"
        vendor_name = "AWS"

        # Override specific rules:
        rule_action_override {
          name = "SizeRestrictions_BODY"
          action_to_use { allow {} }    # Dozvoli large request bodies (file upload)
        }
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "CommonRuleSet"
      sampled_requests_enabled   = true
    }
  }

  # Known Bad Inputs: Log4j, SSRF, Spring4Shell
  rule {
    name     = "AWSManagedRulesKnownBadInputsRuleSet"
    priority = 2
    override_action { none {} }
    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesKnownBadInputsRuleSet"
        vendor_name = "AWS"
      }
    }
    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "KnownBadInputs"
      sampled_requests_enabled   = true
    }
  }

  # IP Reputation: TOR, botovi, scraperi
  rule {
    name     = "AWSManagedRulesAmazonIpReputationList"
    priority = 3
    override_action { none {} }
    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesAmazonIpReputationList"
        vendor_name = "AWS"
      }
    }
    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "IpReputationList"
      sampled_requests_enabled   = true
    }
  }

  # ── Custom Rules ────────────────────────────────────────────────

  # Rate limiting: max 100 req/5min po IP
  rule {
    name     = "RateLimitByIP"
    priority = 10
    action { block {} }
    statement {
      rate_based_statement {
        limit              = 100
        aggregate_key_type = "IP"
      }
    }
    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "RateLimit"
      sampled_requests_enabled   = true
    }
  }

  # Geo-blocking (opcionalno): blokiraj high-risk regije
  # rule {
  #   name = "GeoBlock"
  #   priority = 5
  #   action { block {} }
  #   statement {
  #     geo_match_statement {
  #       country_codes = ["KP", "IR", "SY"]    # Primjer
  #     }
  #   }
  # }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "project-a-waf"
    sampled_requests_enabled   = true
  }
}

# Poveži WAF sa ALB
resource "aws_wafv2_web_acl_association" "main" {
  resource_arn = var.alb_arn
  web_acl_arn  = aws_wafv2_web_acl.main.arn
}

# CloudWatch alarm za WAF blocked requests
resource "aws_cloudwatch_metric_alarm" "waf_blocked" {
  alarm_name          = "project-a-${var.env}-waf-blocked-requests"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "BlockedRequests"
  namespace           = "AWS/WAFV2"
  period              = 300
  statistic           = "Sum"
  threshold           = 100    # Alert ako > 100 blocked req u 5 min
  alarm_description   = "High number of WAF blocked requests"
  alarm_actions       = [var.sns_alerts_arn]

  dimensions = {
    WebACL = aws_wafv2_web_acl.main.name
    Region = var.aws_region
    Rule   = "ALL"
  }
}
```

**WAF Cost:**
```
WAF Web ACL:             $5.00/mj
Per rule (Managed):      $1.00/mj po pravilu
Per 1M requests:         $0.60
Za 3 managed rules + ~1M req:  ~$10/mj ukupno
```

**WAF Mode: Count vs Block:**
```bash
# UVEK počni sa Count mode-om (loguj, ne blokiraj)
# Prati koji zahtjevi bi bili blokirani
# Podesi exclusions/overrides za false-positives
# ZATIM prebaci na Block mode

# U Terraform: override_action { none {} }  = Count + Block
#              override_action { count {} } = samo Count
```

**Monitoring u CloudWatch:**
```
CloudWatch → Metrics → AWS/WAFV2:
- AllowedRequests: normalni zahtjevi
- BlockedRequests: blokirani zahtjevi (pravilima)
- CountedRequests: prebrojani (count mode)

Alarm: BlockedRequests > threshold → Slack notification
```

**Variables:**
```hcl
variable "alb_arn" { type = string }
variable "aws_region" { type = string }
variable "env" { type = string }
variable "sns_alerts_arn" { type = string }
```
