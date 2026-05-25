# Terraform — `18-localstack-aws-local-testing`

**Focus:** Run AWS services locally with LocalStack so you can test Terraform plans and apply cycles without touching a real AWS account or incurring cost.

**Practise focus**

- Install LocalStack via Docker Compose and confirm `awslocal` CLI resolves to `localhost:4566`
- Configure Terraform AWS provider to point at LocalStack endpoint (`endpoint` overrides per service)
- Create S3 bucket, SQS queue, and IAM policy against LocalStack; run `plan → apply → destroy` cycle
- Validate state file reflects local resources identically to real AWS flow
- Understand LocalStack free tier limits vs Pro (which services need Pro licence)
- Use LocalStack for CI pipeline dry-runs — catch resource misconfigurations before they hit staging
- Teardown and reset LocalStack state between test runs
