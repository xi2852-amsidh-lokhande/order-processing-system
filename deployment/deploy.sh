#!/bin/bash

# Order Processing System - SAM Deployment Script
# This script automates the build and deployment process

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="order-processing-system"
DEFAULT_ENVIRONMENT="dev"
DEFAULT_REGION="us-east-1"

# Function to print colored output
print_message() {
    echo -e "${2:-$GREEN}$1${NC}"
}

print_error() {
    echo -e "${RED}ERROR: $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}WARNING: $1${NC}"
}

print_info() {
    echo -e "${BLUE}INFO: $1${NC}"
}

# Function to check prerequisites
check_prerequisites() {
    print_info "Checking prerequisites..."
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI is not installed. Please install it first."
        exit 1
    fi
    
    # Check SAM CLI
    if ! command -v sam &> /dev/null; then
        print_error "SAM CLI is not installed. Please install it first."
        exit 1
    fi
    
    # Check Python
    if ! command -v python &> /dev/null && ! command -v python3 &> /dev/null; then
        print_error "Python is not installed. Please install Python 3.9+ first."
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS credentials are not configured. Run 'aws configure' first."
        exit 1
    fi
    
    print_message "✓ All prerequisites met"
}

# Function to validate SAM template
validate_template() {
    print_info "Validating SAM template..."
    cd deployment
    if sam validate --template template.yaml; then
        print_message "✓ Template validation successful"
    else
        print_error "Template validation failed"
        exit 1
    fi
    cd ..
}

# Function to build the application
build_application() {
    print_info "Building SAM application..."
    cd deployment
    if sam build --template template.yaml --cached --parallel; then
        print_message "✓ Build successful"
    else
        print_error "Build failed"
        exit 1
    fi
    cd ..
}

# Function to deploy the application
deploy_application() {
    local environment=${1:-$DEFAULT_ENVIRONMENT}
    local guided=${2:-false}
    
    print_info "Deploying to environment: $environment"
    cd deployment
    
    if [ "$guided" = true ]; then
        print_info "Running guided deployment..."
        sam deploy --guided
    else
        if [ "$environment" = "dev" ]; then
            sam deploy
        else
            sam deploy --config-env "$environment"
        fi
    fi
    
    if [ $? -eq 0 ]; then
        print_message "✓ Deployment successful"
        get_outputs "$environment"
    else
        print_error "Deployment failed"
        exit 1
    fi
    cd ..
}

# Function to get stack outputs
get_outputs() {
    local environment=${1:-$DEFAULT_ENVIRONMENT}
    local stack_name="${PROJECT_NAME}-${environment}"
    
    print_info "Getting stack outputs..."
    
    # Get API URL
    local api_url=$(aws cloudformation describe-stacks \
        --stack-name "$stack_name" \
        --query 'Stacks[0].Outputs[?OutputKey==`OrderProcessingAPIUrl`].OutputValue' \
        --output text 2>/dev/null)
    
    if [ -n "$api_url" ]; then
        print_message "API Gateway URL: $api_url"
    fi
    
    # Get table names
    local orders_table=$(aws cloudformation describe-stacks \
        --stack-name "$stack_name" \
        --query 'Stacks[0].Outputs[?OutputKey==`OrdersTableName`].OutputValue' \
        --output text 2>/dev/null)
    
    if [ -n "$orders_table" ]; then
        print_message "Orders Table: $orders_table"
    fi
    
    # Get event bus name
    local event_bus=$(aws cloudformation describe-stacks \
        --stack-name "$stack_name" \
        --query 'Stacks[0].Outputs[?OutputKey==`EventBusName`].OutputValue' \
        --output text 2>/dev/null)
    
    if [ -n "$event_bus" ]; then
        print_message "Event Bus: $event_bus"
    fi
}

# Function to test the deployment
test_deployment() {
    local environment=${1:-$DEFAULT_ENVIRONMENT}
    local stack_name="${PROJECT_NAME}-${environment}"
    
    print_info "Testing deployment..."
    
    # Get API URL
    local api_url=$(aws cloudformation describe-stacks \
        --stack-name "$stack_name" \
        --query 'Stacks[0].Outputs[?OutputKey==`OrderProcessingAPIUrl`].OutputValue' \
        --output text 2>/dev/null)
    
    if [ -z "$api_url" ]; then
        print_error "Could not get API URL from stack outputs"
        return 1
    fi
    
    print_info "Testing API endpoint: ${api_url}orders"
    
    # Test order placement
    local response=$(curl -s -w "%{http_code}" -X POST "${api_url}orders" \
        -H "Content-Type: application/json" \
        -H "Authorization: Basic YWRtaW46" \
        -d '{
            "customerId": "test-customer",
            "items": [
                {"vendorId": "test-vendor", "productId": "test-product", "quantity": 1}
            ]
        }')
    
    local http_code="${response: -3}"
    local body="${response%???}"
    
    if [ "$http_code" = "201" ] || [ "$http_code" = "200" ]; then
        print_message "✓ API test successful (HTTP $http_code)"
        print_info "Response: $body"
    else
        print_warning "API test returned HTTP $http_code"
        print_info "Response: $body"
    fi
}

# Function to clean up resources
cleanup() {
    local environment=${1:-$DEFAULT_ENVIRONMENT}
    local stack_name="${PROJECT_NAME}-${environment}"
    
    print_warning "This will delete the entire stack: $stack_name"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "Deleting stack: $stack_name"
        aws cloudformation delete-stack --stack-name "$stack_name"
        print_message "✓ Stack deletion initiated"
    else
        print_info "Cleanup cancelled"
    fi
}

# Function to show logs
show_logs() {
    local function_name=${1:-"OrderHandler"}
    local environment=${2:-$DEFAULT_ENVIRONMENT}
    
    print_info "Showing logs for $function_name in $environment environment..."
    cd deployment
    sam logs -n "$function_name" --stack-name "${PROJECT_NAME}-${environment}" --tail
    cd ..
}

# Function to start local API
start_local() {
    print_info "Starting local API..."
    cd deployment
    sam local start-api --template template.yaml --port 3000
    cd ..
}

# Function to show help
show_help() {
    echo "Order Processing System - SAM Deployment Script"
    echo ""
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  build                    Build the SAM application"
    echo "  deploy [env] [--guided]  Deploy to specified environment (default: dev)"
    echo "  test [env]               Test the deployed API (default: dev)"
    echo "  logs [function] [env]    Show logs for a specific function"
    echo "  local                    Start local API server"
    echo "  cleanup [env]            Delete the stack (default: dev)"
    echo "  validate                 Validate the SAM template"
    echo "  outputs [env]            Show stack outputs (default: dev)"
    echo "  help                     Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 deploy                # Deploy to dev environment"
    echo "  $0 deploy prod           # Deploy to production environment"
    echo "  $0 deploy dev --guided   # Deploy with guided mode"
    echo "  $0 test staging          # Test staging environment"
    echo "  $0 logs OrderHandler dev # Show order handler logs"
    echo "  $0 cleanup prod          # Delete production stack"
    echo ""
    echo "Environments: dev (default), staging, prod"
}

# Main script logic
main() {
    case "${1:-help}" in
        "build")
            check_prerequisites
            validate_template
            build_application
            ;;
        "deploy")
            check_prerequisites
            validate_template
            build_application
            if [ "$3" = "--guided" ]; then
                deploy_application "$2" true
            else
                deploy_application "$2" false
            fi
            ;;
        "test")
            test_deployment "$2"
            ;;
        "logs")
            show_logs "$2" "$3"
            ;;
        "local")
            check_prerequisites
            validate_template
            build_application
            start_local
            ;;
        "cleanup")
            cleanup "$2"
            ;;
        "validate")
            check_prerequisites
            validate_template
            ;;
        "outputs")
            get_outputs "$2"
            ;;
        "help"|"--help"|"-h")
            show_help
            ;;
        *)
            print_error "Unknown command: $1"
            show_help
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
