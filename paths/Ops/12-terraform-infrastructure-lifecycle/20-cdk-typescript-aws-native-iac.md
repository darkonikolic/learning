# Terraform — `20-cdk-typescript-aws-native-iac`

**Focus:** Understand AWS CDK as an alternative IaC surface — write infrastructure in TypeScript, synthesise to CloudFormation, and know when CDK fits over Terraform.

**Practise focus**

- Bootstrap a CDK app: `cdk init app --language typescript`, understand `App → Stack → Construct` hierarchy
- Define an S3 bucket and Lambda function in CDK; run `cdk synth` and read the generated CloudFormation template
- `cdk deploy` to a real AWS account; observe CloudFormation stack creation in the console
- Understand L1 (raw CFN), L2 (opinionated constructs), L3 (patterns) abstraction levels
- Compare CDK vs Terraform: CDK wins on AWS-native constructs and type safety; Terraform wins on multi-cloud and state portability
- When to use both together: Terraform for foundational infra (VPC, IAM), CDK for application-level AWS resources
- `cdk diff` as the CDK equivalent of `terraform plan`
- Destroy stack cleanly: `cdk destroy`
