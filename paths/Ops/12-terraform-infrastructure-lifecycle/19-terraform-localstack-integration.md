# Terraform — `19-terraform-localstack-integration`

**Focus:** Wire a real Terraform module (VPC + EC2 + RDS shape) to LocalStack and validate the full apply/destroy lifecycle locally before promoting to real AWS.

**Practise focus**

- Parameterise AWS provider with a variable flag (`local_mode = true`) that switches endpoints to LocalStack vs real AWS
- Apply the VPC + subnets + security group module against LocalStack; inspect created resources via `awslocal ec2 describe-vpcs`
- Simulate drift: manually delete a resource in LocalStack, run `terraform refresh`, observe plan diff
- Run `terraform plan` in CI against LocalStack as a mandatory gate before any `apply` reaches staging
- Debug provider errors specific to LocalStack (partial service support, eventual consistency quirks)
- Document the handoff boundary: what LocalStack validates vs what only real AWS can catch (IAM propagation delays, quota limits)
