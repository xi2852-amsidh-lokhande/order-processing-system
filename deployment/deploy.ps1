# Order Processing System - SAM Deployment Script (PowerShell)
# This script automates the build and deployment process for Windows

param(
    [Parameter(Position=0)]
    [string]$Command = "help",
    [Parameter(Position=1)]
    [string]$Environment = "dev",
    [Parameter(Position=2)]
    [string]$Option = ""
)

# Configuration
$ProjectName = "order-processing-system"
$DefaultEnvironment = "dev"
$DefaultRegion = "us-east-1"

# Function to print colored output
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "Green"
    )
    Write-Host $Message -ForegroundColor $Color
}

function Write-Error-Custom {
    param([string]$Message)
    Write-Host "ERROR: $Message" -ForegroundColor Red
}

function Write-Warning-Custom {
    param([string]$Message)
    Write-Host "WARNING: $Message" -ForegroundColor Yellow
}

function Write-Info {
    param([string]$Message)
    Write-Host "INFO: $Message" -ForegroundColor Blue
}

# Function to check prerequisites
function Test-Prerequisites {
    Write-Info "Checking prerequisites..."
    
    # Check AWS CLI
    try {
        $null = Get-Command aws -ErrorAction Stop
    }
    catch {
        Write-Error-Custom "AWS CLI is not installed. Please install it first."
        exit 1
    }
    
    # Check SAM CLI
    try {
        $null = Get-Command sam -ErrorAction Stop
    }
    catch {
        Write-Error-Custom "SAM CLI is not installed. Please install it first."
        exit 1
    }
    
    # Check Python
    try {
        $null = Get-Command python -ErrorAction Stop
    }
    catch {
        try {
            $null = Get-Command python3 -ErrorAction Stop
        }
        catch {
            Write-Error-Custom "Python is not installed. Please install Python 3.9+ first."
            exit 1
        }
    }
    
    # Check AWS credentials
    try {
        $null = aws sts get-caller-identity 2>$null
        if ($LASTEXITCODE -ne 0) {
            throw "AWS credentials not configured"
        }
    }
    catch {
        Write-Error-Custom "AWS credentials are not configured. Run 'aws configure' first."
        exit 1
    }
    
    Write-ColorOutput "✓ All prerequisites met"
}

# Function to validate SAM template
function Test-SamTemplate {
    Write-Info "Validating SAM template..."
    Set-Location deployment
    
    $result = sam validate --template template.yaml
    if ($LASTEXITCODE -eq 0) {
        Write-ColorOutput "✓ Template validation successful"
    }
    else {
        Write-Error-Custom "Template validation failed"
        Set-Location ..
        exit 1
    }
    Set-Location ..
}

# Function to build the application
function Build-Application {
    Write-Info "Building SAM application..."
    Set-Location deployment
    
    $result = sam build --template template.yaml --cached --parallel
    if ($LASTEXITCODE -eq 0) {
        Write-ColorOutput "✓ Build successful"
    }
    else {
        Write-Error-Custom "Build failed"
        Set-Location ..
        exit 1
    }
    Set-Location ..
}

# Function to deploy the application
function Deploy-Application {
    param(
        [string]$env = $DefaultEnvironment,
        [bool]$guided = $false
    )
    
    Write-Info "Deploying to environment: $env"
    Set-Location deployment
    
    if ($guided) {
        Write-Info "Running guided deployment..."
        sam deploy --guided
    }
    else {
        if ($env -eq "dev") {
            sam deploy
        }
        else {
            sam deploy --config-env $env
        }
    }
    
    if ($LASTEXITCODE -eq 0) {
        Write-ColorOutput "✓ Deployment successful"
        Get-StackOutputs $env
    }
    else {
        Write-Error-Custom "Deployment failed"
        Set-Location ..
        exit 1
    }
    Set-Location ..
}

# Function to get stack outputs
function Get-StackOutputs {
    param([string]$env = $DefaultEnvironment)
    
    $stackName = "$ProjectName-$env"
    Write-Info "Getting stack outputs..."
    
    # Get API URL
    try {
        $apiUrl = aws cloudformation describe-stacks --stack-name $stackName --query 'Stacks[0].Outputs[?OutputKey==`OrderProcessingAPIUrl`].OutputValue' --output text 2>$null
        if ($apiUrl -and $apiUrl -ne "None") {
            Write-ColorOutput "API Gateway URL: $apiUrl"
        }
    }
    catch {
        Write-Warning-Custom "Could not retrieve API URL"
    }
    
    # Get table names
    try {
        $ordersTable = aws cloudformation describe-stacks --stack-name $stackName --query 'Stacks[0].Outputs[?OutputKey==`OrdersTableName`].OutputValue' --output text 2>$null
        if ($ordersTable -and $ordersTable -ne "None") {
            Write-ColorOutput "Orders Table: $ordersTable"
        }
    }
    catch {
        Write-Warning-Custom "Could not retrieve Orders table name"
    }
    
    # Get event bus name
    try {
        $eventBus = aws cloudformation describe-stacks --stack-name $stackName --query 'Stacks[0].Outputs[?OutputKey==`EventBusName`].OutputValue' --output text 2>$null
        if ($eventBus -and $eventBus -ne "None") {
            Write-ColorOutput "Event Bus: $eventBus"
        }
    }
    catch {
        Write-Warning-Custom "Could not retrieve Event Bus name"
    }
}

# Function to test the deployment
function Test-Deployment {
    param([string]$env = $DefaultEnvironment)
    
    $stackName = "$ProjectName-$env"
    Write-Info "Testing deployment..."
    
    # Get API URL
    try {
        $apiUrl = aws cloudformation describe-stacks --stack-name $stackName --query 'Stacks[0].Outputs[?OutputKey==`OrderProcessingAPIUrl`].OutputValue' --output text 2>$null
        
        if (-not $apiUrl -or $apiUrl -eq "None") {
            Write-Error-Custom "Could not get API URL from stack outputs"
            return
        }
        
        Write-Info "Testing API endpoint: ${apiUrl}orders"
        
        # Test order placement
        $headers = @{
            'Content-Type' = 'application/json'
            'Authorization' = 'Basic YWRtaW46'
        }
        
        $body = @{
            customerId = "test-customer"
            items = @(
                @{
                    vendorId = "test-vendor"
                    productId = "test-product"
                    quantity = 1
                }
            )
        } | ConvertTo-Json
        
        try {
            $response = Invoke-WebRequest -Uri "${apiUrl}orders" -Method POST -Headers $headers -Body $body -ErrorAction Stop
            Write-ColorOutput "✓ API test successful (HTTP $($response.StatusCode))"
            Write-Info "Response: $($response.Content)"
        }
        catch {
            $statusCode = $_.Exception.Response.StatusCode.Value__
            Write-Warning-Custom "API test returned HTTP $statusCode"
            Write-Info "Error: $($_.Exception.Message)"
        }
    }
    catch {
        Write-Error-Custom "Failed to test deployment: $($_.Exception.Message)"
    }
}

# Function to clean up resources
function Remove-Stack {
    param([string]$env = $DefaultEnvironment)
    
    $stackName = "$ProjectName-$env"
    Write-Warning-Custom "This will delete the entire stack: $stackName"
    
    $confirmation = Read-Host "Are you sure? (y/N)"
    if ($confirmation -eq 'y' -or $confirmation -eq 'Y') {
        Write-Info "Deleting stack: $stackName"
        aws cloudformation delete-stack --stack-name $stackName
        Write-ColorOutput "✓ Stack deletion initiated"
    }
    else {
        Write-Info "Cleanup cancelled"
    }
}

# Function to show logs
function Show-Logs {
    param(
        [string]$functionName = "OrderHandler",
        [string]$env = $DefaultEnvironment
    )
    
    Write-Info "Showing logs for $functionName in $env environment..."
    Set-Location deployment
    sam logs -n $functionName --stack-name "$ProjectName-$env" --tail
    Set-Location ..
}

# Function to start local API
function Start-LocalApi {
    Write-Info "Starting local API..."
    Set-Location deployment
    sam local start-api --template template.yaml --port 3000
    Set-Location ..
}

# Function to show help
function Show-Help {
    Write-Host "Order Processing System - SAM Deployment Script (PowerShell)" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Usage: .\deploy.ps1 [COMMAND] [ENVIRONMENT] [OPTION]" -ForegroundColor White
    Write-Host ""
    Write-Host "Commands:" -ForegroundColor Yellow
    Write-Host "  build                    Build the SAM application"
    Write-Host "  deploy [env] [guided]    Deploy to specified environment (default: dev)"
    Write-Host "  test [env]               Test the deployed API (default: dev)"
    Write-Host "  logs [function] [env]    Show logs for a specific function"
    Write-Host "  local                    Start local API server"
    Write-Host "  cleanup [env]            Delete the stack (default: dev)"
    Write-Host "  validate                 Validate the SAM template"
    Write-Host "  outputs [env]            Show stack outputs (default: dev)"
    Write-Host "  help                     Show this help message"
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor Green
    Write-Host "  .\deploy.ps1 deploy                # Deploy to dev environment"
    Write-Host "  .\deploy.ps1 deploy prod           # Deploy to production environment"
    Write-Host "  .\deploy.ps1 deploy dev guided     # Deploy with guided mode"
    Write-Host "  .\deploy.ps1 test staging          # Test staging environment"
    Write-Host "  .\deploy.ps1 logs OrderHandler dev # Show order handler logs"
    Write-Host "  .\deploy.ps1 cleanup prod          # Delete production stack"
    Write-Host ""
    Write-Host "Environments: dev (default), staging, prod" -ForegroundColor Magenta
}

# Main script logic
switch ($Command.ToLower()) {
    "build" {
        Test-Prerequisites
        Test-SamTemplate
        Build-Application
    }
    "deploy" {
        Test-Prerequisites
        Test-SamTemplate
        Build-Application
        if ($Option -eq "guided") {
            Deploy-Application $Environment $true
        }
        else {
            Deploy-Application $Environment $false
        }
    }
    "test" {
        Test-Deployment $Environment
    }
    "logs" {
        Show-Logs $Environment $Option
    }
    "local" {
        Test-Prerequisites
        Test-SamTemplate
        Build-Application
        Start-LocalApi
    }
    "cleanup" {
        Remove-Stack $Environment
    }
    "validate" {
        Test-Prerequisites
        Test-SamTemplate
    }
    "outputs" {
        Get-StackOutputs $Environment
    }
    "help" {
        Show-Help
    }
    default {
        Write-Error-Custom "Unknown command: $Command"
        Show-Help
        exit 1
    }
}
