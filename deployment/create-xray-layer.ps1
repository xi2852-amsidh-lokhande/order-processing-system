# PowerShell script to create and deploy X-Ray layer for distributed tracing

Write-Host "Creating X-Ray auto-instrumentation layer..." -ForegroundColor Green

# Create layer directory structure
New-Item -ItemType Directory -Force -Path "layer\python\lib\python3.13\site-packages" | Out-Null
New-Item -ItemType Directory -Force -Path "temp_layer" | Out-Null

try {
    # Install X-Ray SDK in the layer
    Write-Host "Installing AWS X-Ray SDK..." -ForegroundColor Yellow
    pip install aws-xray-sdk -t "layer\python\lib\python3.13\site-packages" --quiet

    # Copy our custom X-Ray initialization script
    Copy-Item "..\xray_layer\xray_init.py" "layer\python\lib\python3.13\site-packages\"
    Write-Host "Added custom X-Ray initialization script" -ForegroundColor Green

    # Create the layer zip file
    Write-Host "Creating layer zip file..." -ForegroundColor Yellow
    Set-Location "layer"
    Compress-Archive -Path ".\*" -DestinationPath "..\xray-layer.zip" -Force
    Set-Location ".."

    # Set bucket name
    $PROJECT_NAME = if ($env:PROJECT_NAME) { $env:PROJECT_NAME } else { 'order-processing-system' }
    $ENVIRONMENT = if ($env:ENVIRONMENT) { $env:ENVIRONMENT } else { 'dev' }
    $BUCKET_NAME = "$PROJECT_NAME-$ENVIRONMENT-deployment-bucket"
    
    Write-Host "Bucket name: $BUCKET_NAME" -ForegroundColor Cyan

    # Check if bucket exists, create if not
    $bucketExists = aws s3 ls "s3://$BUCKET_NAME" 2>$null
    if (-not $bucketExists) {
        Write-Host "Creating S3 bucket: $BUCKET_NAME" -ForegroundColor Yellow
        aws s3 mb "s3://$BUCKET_NAME"
    }

    # Upload to S3
    Write-Host "Uploading layer to S3..." -ForegroundColor Yellow
    aws s3 cp "xray-layer.zip" "s3://$BUCKET_NAME/layers/"

    Write-Host "X-Ray layer created and uploaded to S3 successfully!" -ForegroundColor Green
}
catch {
    Write-Error "Error creating X-Ray layer: $_"
    exit 1
}
finally {
    # Clean up
    Write-Host "Cleaning up temporary files..." -ForegroundColor Yellow
    if (Test-Path "layer") { Remove-Item -Recurse -Force "layer" }
    if (Test-Path "temp_layer") { Remove-Item -Recurse -Force "temp_layer" }
    if (Test-Path "xray-layer.zip") { Remove-Item -Force "xray-layer.zip" }
}

Write-Host "X-Ray layer deployment complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Run: sam build" -ForegroundColor White
Write-Host "2. Run: sam deploy --guided" -ForegroundColor White
Write-Host "3. Test: python test_tracing.py" -ForegroundColor White
