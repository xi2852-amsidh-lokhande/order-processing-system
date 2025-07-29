#!/bin/bash
# Script to create and deploy X-Ray layer for distributed tracing

set -e

echo "Creating X-Ray auto-instrumentation layer..."

# Create layer directory structure
mkdir -p layer/python/lib/python3.13/site-packages
mkdir -p temp_layer

# Install X-Ray SDK in the layer
pip install aws-xray-sdk -t layer/python/lib/python3.13/site-packages

# Copy our custom X-Ray initialization script
cp ../xray_layer/xray_init.py layer/python/lib/python3.13/site-packages/

# Create the layer zip file
cd layer
zip -r ../xray-layer.zip .
cd ..

# Upload to S3 (assumes bucket exists)
BUCKET_NAME="${PROJECT_NAME:-order-processing-system}-${ENVIRONMENT:-dev}-deployment-bucket"
aws s3 cp xray-layer.zip s3://$BUCKET_NAME/layers/

echo "X-Ray layer created and uploaded to S3"

# Clean up
rm -rf layer temp_layer xray-layer.zip

echo "X-Ray layer deployment complete!"
