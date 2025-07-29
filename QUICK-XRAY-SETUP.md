# Quick X-Ray Setup Guide

## Fixed PowerShell Script Issue ✅

The PowerShell script has been updated to work with Windows PowerShell 5.1. 

## Simplified Deployment (No Lambda Layer Required)

Since you encountered issues with the layer deployment, here's a simpler approach:

### Option 1: Simplified Setup (Recommended)

1. **Install X-Ray SDK locally**:
   ```powershell
   cd deployment
   .\setup-xray-simple.ps1
   ```

2. **Deploy the infrastructure**:
   ```powershell
   sam build
   sam deploy --guided
   ```

### Option 2: Full Layer Setup (Advanced)

If you want the full layer approach:

1. **Create X-Ray layer**:
   ```powershell
   cd deployment
   .\create-xray-layer.ps1
   ```
   *Note: Script now compatible with PowerShell 5.1*

## What's Already Configured

Your CloudFormation template already has:
- ✅ **Lambda X-Ray Tracing**: `Tracing: Active` for all functions  
- ✅ **X-Ray Permissions**: IAM roles have X-Ray permissions
- ✅ **Environment Variables**: X-Ray configuration set
- ✅ **Auto-Instrumentation**: Environment variables enable automatic tracing

## How It Works

Even without the custom layer, AWS X-Ray will still provide:

1. **Lambda Function Tracing**: Automatic trace generation for all Lambda executions
2. **AWS Service Calls**: DynamoDB, EventBridge calls will be traced via the AWS SDK
3. **Performance Metrics**: Cold starts, duration, memory usage
4. **Error Tracking**: Automatic error capture and analysis

## Next Steps

1. Run the simplified setup: `.\setup-xray-simple.ps1`
2. Deploy: `sam build && sam deploy --guided`
3. Test your APIs to generate traces
4. View traces in AWS X-Ray Console

## Viewing Traces

1. Go to **AWS X-Ray Console**
2. Click **"Traces"** 
3. You should see traces for your Lambda functions
4. Click **"Service map"** to see service interactions

The basic X-Ray integration will work immediately once deployed! 🎉
