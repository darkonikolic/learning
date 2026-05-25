# AWS — `22-ecs-fargate-end-to-end-deploy-lab`

**Focus:** Full hands-on deployment of a containerised application to ECS Fargate — from ECR image push to live HTTPS traffic through ALB and Route53.

**Practise focus**

- Push a Docker image to ECR: `docker build → docker tag → aws ecr get-login-password | docker login → docker push`
- Write a Task Definition (JSON or Terraform): container image, CPU/memory, port mappings, environment variables from Secrets Manager
- Create an ECS Cluster and Service with Fargate launch type; set desired count to 2
- Attach an Application Load Balancer target group; confirm health checks pass before traffic shifts
- Wire Route53 A-record alias to ALB DNS name; verify HTTPS via ACM certificate on ALB listener
- Observe a rolling deployment: update image tag, trigger new service deployment, watch old tasks drain
- Debug a failed task: inspect stopped task reason, CloudWatch Logs (`awslogs` driver), security group mismatches
- Scale service manually then configure Application Auto Scaling on CPU utilisation target
- Destroy cleanly: deregister task definition, delete service, drain and delete cluster
