# Deploy X-Ray Cross-Cutting Concern for DynamoDB Tracing
# This script deploys the solution without requiring any code changes

Write-Host "🎯 Deploying X-Ray Cross-Cutting Concern for DynamoDB Tracing..." -ForegroundColor Green
Write-Host "   No code changes required - applied at infrastructure level" -ForegroundColor Yellow

# Change to deployment directory
Set-Location deployment

# Deploy using SAM
Write-Host "`n📦 Deploying CloudFormation stack..." -ForegroundColor Cyan
sam deploy --confirm-changeset

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ X-Ray DynamoDB tracing deployed successfully!" -ForegroundColor Green
    Write-Host "`n🔍 What's now enabled:" -ForegroundColor White
    Write-Host "   • All Lambda functions have X-Ray tracing active" -ForegroundColor White
    Write-Host "   • AWS X-Ray SDK layer attached (cross-cutting concern)" -ForegroundColor White
    Write-Host "   • boto3 DynamoDB calls automatically traced" -ForegroundColor White
    Write-Host "   • Zero application code changes required" -ForegroundColor White
    
    Write-Host "`n📈 View traces in AWS X-Ray console:" -ForegroundColor Yellow
    Write-Host "   https://console.aws.amazon.com/xray/home" -ForegroundColor Blue
    
    Write-Host "`n🎉 DynamoDB operations will now appear in X-Ray traces!" -ForegroundColor Green
} else {
    Write-Host "`n❌ Deployment failed. Check SAM output above." -ForegroundColor Red
}
