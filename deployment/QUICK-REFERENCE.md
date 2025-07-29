# SAM Deployment Quick Reference

## 🚀 Quick Start (5 minutes)

### Prerequisites Check
```bash
# Verify installations
aws --version
sam --version
python --version

# Check AWS credentials
aws sts get-caller-identity
```

### One-Command Deploy
```bash
# Navigate to deployment folder
cd deployment

# Build and deploy with guided setup (first time)
sam build && sam deploy --guided

# OR use the deployment scripts
./deploy.sh deploy dev --guided    # Linux/Mac
.\deploy.ps1 deploy dev guided     # Windows PowerShell

# OR use Makefile
make deploy-guided                 # Linux/Mac with make
```

## 📋 Deployment Checklist

### Before Deployment
- [ ] AWS CLI installed and configured
- [ ] SAM CLI installed (version 1.x+)
- [ ] Python 3.9+ installed
- [ ] AWS credentials configured (`aws configure`)
- [ ] Sufficient AWS permissions (Lambda, API Gateway, DynamoDB, EventBridge, CloudFormation)

### During First Deployment
- [ ] Run `sam deploy --guided`
- [ ] Choose stack name (default: `order-processing-system-dev`)
- [ ] Confirm region (default: `us-east-1`)
- [ ] Set environment (dev/staging/prod)
- [ ] Allow SAM to create IAM roles (Y)
- [ ] Confirm deployment (Y)

### Post-Deployment
- [ ] Note the API Gateway URL from outputs
- [ ] Create user credentials in AWS Secrets Manager
- [ ] Test API endpoints
- [ ] Verify DynamoDB tables created
- [ ] Check EventBridge bus and rules
- [ ] Test DLQ and replay functionality

## 🔧 Quick Commands

### Build & Deploy
```bash
# Standard deployment
cd deployment
sam build
sam deploy

# With environment
sam deploy --config-env staging

# Full rebuild
sam build --use-container
sam deploy
```

### Testing
```bash
# Get API URL
aws cloudformation describe-stacks \
  --stack-name order-processing-system-dev \
  --query 'Stacks[0].Outputs[?OutputKey==`OrderProcessingAPIUrl`].OutputValue' \
  --output text

# Test order placement
curl -X POST "$API_URL/orders" \
  -H "Content-Type: application/json" \
  -H "Authorization: Basic YWRtaW46" \
  -d '{"customerId":"test","items":[{"vendorId":"v1","productId":"p1","quantity":1}]}'
```

### Monitoring
```bash
# View logs
sam logs -n OrderHandler --tail

# Stack status
aws cloudformation describe-stacks --stack-name order-processing-system-dev

# DynamoDB tables
aws dynamodb list-tables
```

### Cleanup
```bash
# Delete stack
aws cloudformation delete-stack --stack-name order-processing-system-dev

# Delete secrets (if created)
aws secretsmanager delete-secret --secret-id "user/admin" --force-delete-without-recovery
```

## 🏗️ File Structure

```
deployment/
├── template.yaml              # SAM CloudFormation template
├── samconfig.toml            # SAM configuration
├── README-deployment.md      # Detailed deployment guide
├── deploy.sh                 # Linux/Mac deployment script
├── deploy.ps1                # Windows PowerShell script
├── Makefile                  # Make commands for deployment
└── events/                   # Test event files
    ├── test-order-event.json
    ├── test-inventory-event.json
    └── test-payment-event.json
```

## 🔑 Default Credentials

### Basic Auth (username:password)
- **admin:** (empty password) → `Basic YWRtaW46`
- **demo:** (empty password) → `Basic ZGVtbzo=`

### Bearer Token
- **demo-token** → `Bearer demo-token`

### AWS Secrets Manager Setup
```bash
# Create admin user
aws secretsmanager create-secret \
  --name "user/admin" \
  --secret-string '{"password_hash":"e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855","role":"admin"}'

# Create demo user  
aws secretsmanager create-secret \
  --name "user/demo" \
  --secret-string '{"password_hash":"e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855","role":"user"}'
```

## 🌍 Environment Configuration

### Development (default)
- Stack: `order-processing-system-dev`
- Config: `[default]` in samconfig.toml

### Staging
- Stack: `order-processing-system-staging`
- Deploy: `sam deploy --config-env staging`

### Production
- Stack: `order-processing-system-prod`
- Deploy: `sam deploy --config-env production`

## ⚠️ Common Issues & Solutions

### Build Failures
```bash
# Clear cache and rebuild
rm -rf .aws-sam/
sam build --use-container
```

### Deployment Failures
```bash
# Check stack events
aws cloudformation describe-stack-events --stack-name order-processing-system-dev

# Delete failed stack
aws cloudformation delete-stack --stack-name order-processing-system-dev
```

### Permission Issues
- Ensure IAM user/role has CloudFormation, Lambda, API Gateway, DynamoDB permissions
- Check AWS CLI configuration: `aws configure list`

### Lambda Function Errors
```bash
# Check logs
sam logs -n OrderHandler --stack-name order-processing-system-dev

# Local testing
sam local invoke OrderHandler --event events/test-order-event.json
```

## 📊 Resources Created

### AWS Services
- **API Gateway**: REST API with custom authorizer
- **Lambda Functions**: 9 functions (handlers + consumers + authorizer)
- **DynamoDB**: 4 tables (Orders, Inventory, Payments, IdempotencyKeys)
- **EventBridge**: Custom event bus with rules
- **SQS**: 3 DLQ queues for event consumers
- **CloudWatch**: Log groups for all Lambda functions
- **IAM**: Roles and policies for Lambda execution

### Cost Estimation (per month, dev environment)
- **Lambda**: ~$5 (based on 100K invocations)
- **DynamoDB**: ~$2 (pay-per-request, low usage)
- **API Gateway**: ~$3 (per 1M requests)
- **EventBridge**: ~$1 (per 1M events)
- **CloudWatch**: ~$1 (logs retention)
- **Total**: ~$12/month for development usage

## 🎯 Production Readiness

### Security
- [ ] Enable AWS WAF on API Gateway
- [ ] Use custom domain with SSL/TLS
- [ ] Rotate secrets regularly
- [ ] Enable VPC endpoints for DynamoDB

### Performance
- [ ] Configure Lambda provisioned concurrency
- [ ] Optimize DynamoDB capacity settings
- [ ] Enable DynamoDB auto-scaling
- [ ] Set up CloudWatch alarms

### Monitoring
- [ ] Create CloudWatch dashboard
- [ ] Set up error rate alarms
- [ ] Enable AWS X-Ray tracing
- [ ] Configure log aggregation

### Backup & Recovery
- [ ] Enable DynamoDB point-in-time recovery
- [ ] Set up cross-region backups
- [ ] Document disaster recovery procedures
