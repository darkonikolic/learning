# AWS — `23-codepipeline-codedeploy-native-ci`

**Focus:** Build an AWS-native CI/CD pipeline using CodePipeline + CodeBuild + CodeDeploy — the deployment surface you encounter in AWS-first organisations.

**Practise focus**

- Understand the three stages: Source (CodeCommit/GitHub) → Build (CodeBuild) → Deploy (CodeDeploy/ECS)
- Write a `buildspec.yml`: install phase, build phase (docker build + push to ECR), post-build phase (update task definition)
- Configure CodeBuild project with an IAM role scoped to ECR push and S3 artifact write
- Create a CodePipeline with GitHub v2 source connection; trigger pipeline on push to `main`
- Deploy to ECS using CodeDeploy blue/green: configure `AppSpec` for ECS task definition swap
- Observe blue/green traffic shift in ALB listener rules; verify rollback on failed health check
- Compare: CodePipeline vs GitLab CI for ECS deploy — native IAM integration vs flexibility
- Add a manual approval action between staging and production stages
