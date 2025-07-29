#!/bin/bash

# Build and deploy X-Ray auto-patching Lambda Layer
# This creates a cross-cutting concern for DynamoDB X-Ray tracing without code changes

LAYER_DIR="xray-layer"
DEPLOYMENT_DIR="deployment"
BUCKET_PREFIX="order-processing-system"
REGION="us-east-1"

echo "Building X-Ray Auto-Patching Lambda Layer..."

# Change to deployment directory
cd $DEPLOYMENT_DIR

# Create layer zip
cd $LAYER_DIR
zip -r ../xray-autopatch-layer.zip python/
cd ..

echo "Layer package created: xray-autopatch-layer.zip"

# Check if S3 bucket exists, if not create deployment instructions
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>/dev/null)
if [ $? -eq 0 ]; then
    BUCKET_NAME="${BUCKET_PREFIX}-dev-xray-layer-${ACCOUNT_ID}"
    echo "Deploying to S3 bucket: $BUCKET_NAME"
    
    # Create bucket if it doesn't exist
    aws s3 mb s3://$BUCKET_NAME --region $REGION 2>/dev/null || true
    
    # Upload layer
    aws s3 cp xray-autopatch-layer.zip s3://$BUCKET_NAME/
    
    echo "✅ Layer uploaded to S3"
    echo "Now run: sam deploy"
    
else
    echo "⚠️  AWS CLI not configured. Manual steps required:"
    echo "1. Create S3 bucket: ${BUCKET_PREFIX}-dev-xray-layer-{your-account-id}"
    echo "2. Upload xray-autopatch-layer.zip to the bucket"
    echo "3. Run: sam deploy"
fi

echo ""
echo "🎯 X-Ray DynamoDB tracing will now work automatically without code changes!"
echo "   All boto3 DynamoDB calls will be traced in X-Ray"
