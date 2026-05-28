# 05 — AWS SQS alternativa

## Kada AWS SQS > Redis Streams

| Kriterij | Redis Streams | AWS SQS |
|----------|--------------|---------|
| At-least-once delivery | Da (manual XACK) | Da (managed) |
| Dead Letter Queue | Ručno implementirati | Ugrađeno |
| Message retention | Redis memory (kratko) | 14 dana na disku |
| Throughput | Visok (single Redis node) | Praktički neograničen |
| Cost | Dio Redis infrastrukture | $0.40/million poruka |
| Visibility timeout | XPENDING + MinIdle | SQS Console + API |
| Cross-service / cross-account | Ne | Da |
| Fanout (SNS → SQS) | Ne | Da |
| Setup kompleksnost | Nizak (vec imas Redis) | Srednji (Terraform) |

**Za project-a:** Redis Streams je dovoljan — već imaš Redis za cache, nema dodatnih troškova ni konfiguracije.

**Prelazak na SQS ima smisla kada:**
- Trebaš cross-account dostavu poruka (npr. iz mikroservisa u drugi AWS account)
- Potrebna ti je garantovana 14-dnevna retencija bez brige o Redis memoriji
- Trebaš fanout: jedna poruka → više SQS queue-ova (via SNS)
- Redis postaje bottleneck (single-node limit)

---

## Terraform za SQS

```hcl
# terraform/modules/sqs/main.tf

resource "aws_sqs_queue" "email" {
  name                       = "project-a-email-queue"
  delay_seconds              = 0
  max_message_size           = 65536    # 64 KB — dovoljno za email payload
  message_retention_seconds  = 86400    # 1 dan (default 4 dana)
  receive_wait_time_seconds  = 20       # Long polling — smanjuje prazne API pozive
  visibility_timeout_seconds = 30       # Koliko worker ima da procesira poruku

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.email_dead.arn
    maxReceiveCount     = 3   # Nakon 3 neuspjela pokušaja → dead letter
  })

  tags = {
    Project     = "project-a"
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

resource "aws_sqs_queue" "email_dead" {
  name                      = "project-a-email-dead-queue"
  message_retention_seconds = 1209600   # 14 dana — za ručnu inspekciju

  tags = {
    Project     = "project-a"
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

# CloudWatch alarm za dead letter queue
resource "aws_cloudwatch_metric_alarm" "dead_letter_not_empty" {
  alarm_name          = "project-a-email-dead-letter-not-empty"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = 300
  statistic           = "Sum"
  threshold           = 0
  alarm_description   = "Dead letter queue ima poruka — potrebna ručna inspekcija"

  dimensions = {
    QueueName = aws_sqs_queue.email_dead.name
  }

  alarm_actions = [var.sns_alert_topic_arn]
}

# IAM policy za Go service (IRSA)
resource "aws_iam_policy" "sqs_email_producer" {
  name = "project-a-sqs-email-producer"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["sqs:SendMessage", "sqs:GetQueueUrl"]
      Resource = aws_sqs_queue.email.arn
    }]
  })
}

resource "aws_iam_policy" "sqs_email_consumer" {
  name = "project-a-sqs-email-consumer"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "sqs:ReceiveMessage",
        "sqs:DeleteMessage",
        "sqs:GetQueueAttributes",
        "sqs:ChangeMessageVisibility",
      ]
      Resource = aws_sqs_queue.email.arn
    }]
  })
}
```

---

## Go SQS producer

```go
package queue

import (
	"context"
	"encoding/json"
	"fmt"

	"github.com/aws/aws-sdk-go-v2/aws"
	"github.com/aws/aws-sdk-go-v2/service/sqs"
)

type SQSProducer struct {
	client   *sqs.Client
	queueURL string
}

func NewSQSProducer(client *sqs.Client, queueURL string) *SQSProducer {
	return &SQSProducer{client: client, queueURL: queueURL}
}

func (p *SQSProducer) PublishEmailEvent(ctx context.Context, event EmailEvent) error {
	data, err := json.Marshal(event)
	if err != nil {
		return fmt.Errorf("marshal event: %w", err)
	}

	_, err = p.client.SendMessage(ctx, &sqs.SendMessageInput{
		QueueUrl:    aws.String(p.queueURL),
		MessageBody: aws.String(string(data)),
		// MessageGroupId za FIFO queue (opcionalno)
		// MessageDeduplicationId za FIFO (opcionalno)
	})
	if err != nil {
		return fmt.Errorf("sqs send message: %w", err)
	}

	return nil
}
```

---

## Go SQS consumer

```go
package worker

import (
	"context"
	"encoding/json"
	"fmt"
	"time"

	"github.com/aws/aws-sdk-go-v2/aws"
	"github.com/aws/aws-sdk-go-v2/service/sqs"
	"github.com/aws/aws-sdk-go-v2/service/sqs/types"
	"go.uber.org/zap"
)

type SQSWorker struct {
	sqs      *sqs.Client
	queueURL string
	email    EmailService
	logger   *zap.Logger
}

func (w *SQSWorker) Start(ctx context.Context) error {
	w.logger.Info("SQS worker started", zap.String("queue", w.queueURL))

	for {
		select {
		case <-ctx.Done():
			return nil
		default:
			if err := w.poll(ctx); err != nil {
				w.logger.Error("poll error", zap.Error(err))
				time.Sleep(5 * time.Second)
			}
		}
	}
}

func (w *SQSWorker) poll(ctx context.Context) error {
	out, err := w.sqs.ReceiveMessage(ctx, &sqs.ReceiveMessageInput{
		QueueUrl:            aws.String(w.queueURL),
		MaxNumberOfMessages: 10,
		WaitTimeSeconds:     20,    // Long polling
		VisibilityTimeout:   30,    // 30s za procesiranje
	})
	if err != nil {
		return fmt.Errorf("receive message: %w", err)
	}

	for _, msg := range out.Messages {
		if err := w.process(ctx, msg); err != nil {
			w.logger.Error("process message error",
				zap.String("id", aws.ToString(msg.MessageId)),
				zap.Error(err),
			)
			// Bez DeleteMessage → SQS automatski vraća poruku u queue
			// Nakon maxReceiveCount → ide u dead letter (konfigurirano Terraformom)
		}
	}
	return nil
}

func (w *SQSWorker) process(ctx context.Context, msg types.Message) error {
	var event queue.EmailEvent
	if err := json.Unmarshal([]byte(aws.ToString(msg.Body)), &event); err != nil {
		// Neispravan format — brišemo da ne blokira queue
		_ = w.deleteMessage(ctx, msg)
		return nil
	}

	if err := w.sendEmail(ctx, event); err != nil {
		return err  // Ne brišemo → SQS retry
	}

	// Uspjeh — eksplicitno briši iz queue-a
	return w.deleteMessage(ctx, msg)
}

func (w *SQSWorker) deleteMessage(ctx context.Context, msg types.Message) error {
	_, err := w.sqs.DeleteMessage(ctx, &sqs.DeleteMessageInput{
		QueueUrl:      aws.String(w.queueURL),
		ReceiptHandle: msg.ReceiptHandle,
	})
	return err
}
```

---

## Usporedba arhitektura za project-a

```
Trenutna arhitektura (Redis Streams):
  Go API → XADD → Redis Stream → XREADGROUP → Go Worker → AWS SES
  
  Prednosti: jednostavno, jeftino, isti Redis za cache
  Mana: Redis memory limit, ručni DLQ

SQS arhitektura:
  Go API → SendMessage → SQS → ReceiveMessage → Go Worker → AWS SES
                                    ↓ (after 3 fails)
                               SQS Dead Letter Queue
  
  Prednosti: managed DLQ, CloudWatch monitoring, 14-dnevna retencija
  Mana: dodatna infrastruktura, AWS vendor lock-in
```

**Preporuka za project-a:** ostani na Redis Streams dok ne dostigneš >100k emailova/dan
ili dok ne trebaš cross-service fanout. Do tada Redis Streams pokriva sve potrebe
uz nultu dodatnu infrastrukturnu kompleksnost.
