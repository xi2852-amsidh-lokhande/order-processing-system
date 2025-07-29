# SAM Deployment Guide - Order Processing System

This guide provides step-by-step instructions for deploying the Order Processing System using AWS SAM (Serverless Application Model).

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Project Structure](#project-structure)
3. [Configuration](#configuration)
4. [Pre-Deployment Setup](#pre-deployment-setup)
5. [Deployment Steps](#deployment-steps)
6. [Post-Deployment Configuration](#post-deployment-configuration)
7. [Testing the Deployment](#testing-the-deployment)
8. [Environment Management](#environment-management)
9. [Troubleshooting](#troubleshooting)
10. [Cleanup](#cleanup)

## Prerequisites

### Required Tools
- **AWS CLI v2.x**: [Installation Guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
- **SAM CLI v1.x**: [Installation Guide](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html)
- **Python 3.9+**: [Download Python](https://www.python.org/downloads/)
- **Git**: [Download Git](https://git-scm.com/)

### AWS Account Setup
- AWS Account with appropriate permissions
- AWS CLI configured with credentials
- S3 bucket for SAM deployments (will be created automatically)

### Verify Prerequisites
```bash
# Check AWS CLI
aws --version
aws sts get-caller-identity

# Check SAM CLI
sam --version

# Check Python
python --version
```

## Project Structure

```
order-processing-system/
├── deployment/
│   ├── template.yaml          # SAM CloudFormation template
│   ├── samconfig.toml         # SAM configuration file
│   └── README-deployment.md   # This file
├── src/                       # Lambda function source code
│   ├── handlers/
│   ├── services/
│   ├── dao/
│   └── common/
├── events/
│   └── consumers/
├── authorizers/
└── requirements.txt
```

## Configuration

### 1. Update SAM Configuration
Edit `deployment/samconfig.toml` if needed:

```toml
[default.deploy.parameters]
region = "us-east-1"  # Change to your preferred region
parameter_overrides = [
    "Environment=dev",
    "ProjectName=order-processing-system"  # Change if needed
]
```

### 2. Environment Variables
The template automatically sets up the following environment variables for Lambda functions:
- `ORDERS_TABLE`
- `INVENTORY_TABLE`
- `PAYMENTS_TABLE`
- `IDEMPOTENCY_TABLE`
- `EVENT_BUS_NAME`
- `AUTH_TOKEN`
- `AWS_REGION`

## Pre-Deployment Setup

### 1. Navigate to Project Root
```bash
cd /path/to/order-processing-system
```

### 2. Install Dependencies (Optional - for local testing)
```bash
pip install -r requirements.txt
```

### 3. Validate SAM Template
```bash
cd deployment
sam validate --template template.yaml
```

### 4. Configure AWS Credentials
```bash
aws configure
# Enter your AWS Access Key ID, Secret Access Key, Region, and Output format
```

## Deployment Steps

### Step 1: Build the Application
```bash
cd deployment
sam build --template template.yaml
```

**Expected Output:**
```
Build Succeeded

Built Artifacts  : .aws-sam/build
Built Template   : .aws-sam/build/template.yaml
```

### Step 2: Deploy to AWS (First Time)
```bash
sam deploy --guided
```

**Follow the prompts:**
```
Configuring SAM deploy
======================

Looking for config file [samconfig.toml] :  Found
Reading default arguments  :  Success

Setting default arguments for 'sam deploy'
=========================================
Stack Name [order-processing-system-dev]: 
AWS Region [us-east-1]: 
Parameter Environment [dev]: 
Parameter ProjectName [order-processing-system]: 
#Shows you resources changes to be deployed and require a 'Y' to initiate deploy
Confirm changes before deploy [Y/n]: Y
#SAM needs permission to be able to create roles to connect to the resources in your template
Allow SAM CLI to create IAM roles [Y/n]: Y
#Preserves the state of previously provisioned resources when an operation fails
Disable rollback [y/N]: N
CustomAuthorizer may not have authorization defined, Is this okay? [y/N]: Y
OrderHandler may not have authorization defined, Is this okay? [y/N]: Y
InventoryHandler may not have authorization defined, Is this okay? [y/N]: Y
PaymentHandler may not have authorization defined, Is this okay? [y/N]: Y
Save parameters to config file [Y/n]: Y
SAM configuration file [samconfig.toml]: 
SAM configuration environment [default]: 

Deploy this changeset? [y/N]: y
```

### Step 3: Subsequent Deployments
For future deployments, simply run:
```bash
sam deploy
```

### Step 4: Monitor Deployment
```bash
# Watch CloudFormation stack events
aws cloudformation describe-stack-events --stack-name order-processing-system-dev
```

## Post-Deployment Configuration

### 1. Set Up User Credentials in AWS Secrets Manager

Create sample user credentials for the Lambda authorizer:

```bash
# Create admin user
aws secretsmanager create-secret \
    --name "user/admin" \
    --description "Admin user credentials" \
    --secret-string '{"password_hash":"e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855","role":"admin"}'

# Create demo user
aws secretsmanager create-secret \
    --name "user/demo" \
    --description "Demo user credentials" \
    --secret-string '{"password_hash":"e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855","role":"user"}'
```

**Note:** The password hashes above are for empty strings. In production, use proper salted hashes.

### 2. Get API Gateway URL
```bash
aws cloudformation describe-stacks \
    --stack-name order-processing-system-dev \
    --query 'Stacks[0].Outputs[?OutputKey==`OrderProcessingAPIUrl`].OutputValue' \
    --output text
```

### 3. Test Lambda Authorizer
The Lambda authorizer supports:
- **Basic Auth**: `Basic YWRtaW46` (admin:empty_password)
- **Bearer Token**: `Bearer demo-token`

## Testing the Deployment

### 1. Test Order Placement
```bash
export API_URL=$(aws cloudformation describe-stacks \
    --stack-name order-processing-system-dev \
    --query 'Stacks[0].Outputs[?OutputKey==`OrderProcessingAPIUrl`].OutputValue' \
    --output text)

# Test with Basic Auth
curl -X POST "${API_URL}orders" \
    -H "Content-Type: application/json" \
    -H "Authorization: Basic YWRtaW46" \
    -d '{
        "customerId": "cust123",
        "items": [
            {"vendorId": "v1", "productId": "p1", "quantity": 2}
        ]
    }'
```

### 2. Test Inventory Update
```bash
curl -X POST "${API_URL}inventory" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer demo-token" \
    -d '{
        "vendorId": "v1",
        "productId": "p1",
        "quantity": 10
    }'
```

### 3. Test Payment Processing
```bash
curl -X POST "${API_URL}payments" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer demo-token" \
    -d '{
        "orderId": "order123",
        "amount": 100,
        "paymentMethod": "credit_card"
    }'
```

### 4. Check DynamoDB Tables
```bash
# List items in Orders table
aws dynamodb scan --table-name order-processing-system-dev-Orders

# List items in Inventory table
aws dynamodb scan --table-name order-processing-system-dev-Inventory

# List items in Payments table
aws dynamodb scan --table-name order-processing-system-dev-Payments
```

### 5. Check EventBridge Events
```bash
# Check CloudWatch Logs for event consumers
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/order-processing-system-dev"
```

## Environment Management

### Deploy to Staging
```bash
sam deploy --config-env staging
```

### Deploy to Production
```bash
sam deploy --config-env production
```

### Custom Environment
```bash
sam deploy --parameter-overrides Environment=custom ProjectName=my-custom-name
```

## Troubleshooting

### Common Issues and Solutions

#### 1. Build Failures
```bash
# Issue: Dependencies not found
# Solution: Install dependencies locally first
pip install -r requirements.txt

# Issue: Python version mismatch
# Solution: Use Python 3.9+ or update runtime in template.yaml
```

#### 2. Deployment Failures
```bash
# Issue: Insufficient permissions
# Solution: Ensure IAM user/role has CloudFormation, Lambda, API Gateway, DynamoDB permissions

# Issue: Stack already exists
# Solution: Delete existing stack or use a different stack name
aws cloudformation delete-stack --stack-name order-processing-system-dev
```

#### 3. Lambda Function Errors
```bash
# Check Lambda logs
sam logs -n OrderHandler --stack-name order-processing-system-dev --tail

# Check specific time range
sam logs -n OrderHandler --stack-name order-processing-system-dev --start-time 2024-01-01T00:00:00
```

#### 4. API Gateway Issues
```bash
# Test Lambda function locally
sam local start-api --template template.yaml

# Test specific function
sam local invoke OrderHandler --event events/test-order-event.json
```

#### 5. DynamoDB Issues
```bash
# Check table status
aws dynamodb describe-table --table-name order-processing-system-dev-Orders

# Check for throttling
aws cloudwatch get-metric-statistics \
    --namespace AWS/DynamoDB \
    --metric-name UserErrors \
    --dimensions Name=TableName,Value=order-processing-system-dev-Orders \
    --start-time 2024-01-01T00:00:00Z \
    --end-time 2024-01-01T23:59:59Z \
    --period 3600 \
    --statistics Sum
```

### Debug Commands
```bash
# Describe stack resources
aws cloudformation describe-stack-resources --stack-name order-processing-system-dev

# Get stack events
aws cloudformation describe-stack-events --stack-name order-processing-system-dev

# Check Lambda function configuration
aws lambda get-function --function-name order-processing-system-dev-order-handler
```

## Performance Optimization

### 1. Lambda Function Optimization
- **Memory**: Adjust memory settings in template.yaml (MemorySize: 512)
- **Timeout**: Adjust timeout settings (Timeout: 30)
- **Cold Start**: Use Provisioned Concurrency for production

### 2. DynamoDB Optimization
- **Read/Write Capacity**: Switch to On-Demand or adjust provisioned capacity
- **Indexes**: Add GSI/LSI for query patterns
- **TTL**: Configure TTL for IdempotencyTable

### 3. EventBridge Optimization
- **Batching**: Adjust batch size for DLQ replay handlers
- **Retry**: Configure retry policies for event rules

## Security Considerations

### 1. API Gateway Security
- Enable AWS WAF
- Add rate limiting
- Configure CORS properly
- Use custom domain with SSL/TLS

### 2. Lambda Security
- Use least privilege IAM policies
- Enable VPC if accessing private resources
- Rotate secrets regularly

### 3. DynamoDB Security
- Enable encryption at rest
- Use VPC endpoints
- Enable point-in-time recovery

## Monitoring and Logging

### 1. CloudWatch Setup
```bash
# Create custom dashboard
aws cloudwatch put-dashboard \
    --dashboard-name "OrderProcessingSystem" \
    --dashboard-body file://dashboard.json
```

### 2. Alarms
```bash
# Create error alarm
aws cloudwatch put-metric-alarm \
    --alarm-name "OrderHandler-Errors" \
    --alarm-description "Lambda function errors" \
    --metric-name Errors \
    --namespace AWS/Lambda \
    --statistic Sum \
    --period 300 \
    --threshold 5 \
    --comparison-operator GreaterThanThreshold \
    --dimensions Name=FunctionName,Value=order-processing-system-dev-order-handler
```

### 3. X-Ray Tracing
Enable in template.yaml:
```yaml
Globals:
  Function:
    Tracing: Active
```

## Cleanup

### Delete Development Stack
```bash
aws cloudformation delete-stack --stack-name order-processing-system-dev
```

### Delete All Environments
```bash
# Delete dev
aws cloudformation delete-stack --stack-name order-processing-system-dev

# Delete staging
aws cloudformation delete-stack --stack-name order-processing-system-staging

# Delete production
aws cloudformation delete-stack --stack-name order-processing-system-prod
```

### Clean Up S3 Buckets (if needed)
```bash
# Find SAM deployment buckets
aws s3 ls | grep sam-

# Delete bucket contents and bucket
aws s3 rm s3://your-sam-bucket --recursive
aws s3 rb s3://your-sam-bucket
```

### Clean Up Secrets Manager
```bash
# Delete user secrets
aws secretsmanager delete-secret --secret-id "user/admin" --force-delete-without-recovery
aws secretsmanager delete-secret --secret-id "user/demo" --force-delete-without-recovery
```

## Additional Resources

- [AWS SAM Documentation](https://docs.aws.amazon.com/serverless-application-model/)
- [AWS Lambda Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)
- [DynamoDB Best Practices](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices.html)
- [EventBridge Best Practices](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-best-practices.html)
- [API Gateway Best Practices](https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-basic-concept.html)

## Support

For issues with this deployment:
1. Check the troubleshooting section above
2. Review CloudFormation events
3. Check Lambda function logs
4. Validate your AWS permissions

---
**Note**: This deployment guide assumes you have the necessary AWS permissions and the source code is properly structured as per the project requirements.
