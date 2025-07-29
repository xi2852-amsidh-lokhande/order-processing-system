# PowerShell script to build and deploy X-Ray auto-patching Lambda Layer
# This creates a cross-cutting concern for DynamoDB X-Ray tracing without code changes

$LAYER_DIR = "xray-layer"
$DEPLOYMENT_DIR = "deployment"
$BUCKET_PREFIX = "order-processing-system"
$REGION = "us-east-1"

Write-Host "Building X-Ray Auto-Patching Lambda Layer..." -ForegroundColor Green

# Change to deployment directory
Set-Location $DEPLOYMENT_DIR

# Create layer zip
Set-Location $LAYER_DIR
Compress-Archive -Path "python\*" -DestinationPath "..\xray-autopatch-layer.zip" -Force
Set-Location ..

Write-Host "Layer package created: xray-autopatch-layer.zip" -ForegroundColor Green

# Check if AWS CLI is available
try {
    $ACCOUNT_ID = aws sts get-caller-identity --query Account --output text 2>$null
    if ($LASTEXITCODE -eq 0) {
        $BUCKET_NAME = "${BUCKET_PREFIX}-dev-xray-layer-${ACCOUNT_ID}"
        Write-Host "Deploying to S3 bucket: $BUCKET_NAME" -ForegroundColor Yellow
        
        # Create bucket if it doesn't exist
        aws s3 mb "s3://$BUCKET_NAME" --region $REGION 2>$null
        
        # Upload layer
        aws s3 cp "xray-autopatch-layer.zip" "s3://$BUCKET_NAME/"
        
        Write-Host "✅ Layer uploaded to S3" -ForegroundColor Green
        Write-Host "Now run: sam deploy" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "⚠️  AWS CLI not configured. Manual steps required:" -ForegroundColor Yellow
    Write-Host "1. Create S3 bucket: ${BUCKET_PREFIX}-dev-xray-layer-{your-account-id}" -ForegroundColor White
    Write-Host "2. Upload xray-autopatch-layer.zip to the bucket" -ForegroundColor White
    Write-Host "3. Run: sam deploy" -ForegroundColor White
}

Write-Host ""
Write-Host "🎯 X-Ray DynamoDB tracing will now work automatically without code changes!" -ForegroundColor Cyan
Write-Host "   All boto3 DynamoDB calls will be traced in X-Ray" -ForegroundColor Cyan
