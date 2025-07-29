#!/bin/bash

# Order Processing System - Post-Deployment Validation Script
# This script validates that all components are working correctly after deployment

set -e

# Configuration
PROJECT_NAME="order-processing-system"
ENVIRONMENT="${1:-dev}"
STACK_NAME="$PROJECT_NAME-$ENVIRONMENT"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== Order Processing System - Post-Deployment Validation ===${NC}"
echo -e "${BLUE}Environment: $ENVIRONMENT${NC}"
echo -e "${BLUE}Stack: $STACK_NAME${NC}"
echo ""

# Function to check if stack exists
check_stack_exists() {
    echo -e "${BLUE}1. Checking CloudFormation stack...${NC}"
    
    STACK_STATUS=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --query 'Stacks[0].StackStatus' \
        --output text 2>/dev/null || echo "NOT_FOUND")
    
    if [ "$STACK_STATUS" = "CREATE_COMPLETE" ] || [ "$STACK_STATUS" = "UPDATE_COMPLETE" ]; then
        echo -e "${GREEN}✓ Stack $STACK_NAME exists and is in $STACK_STATUS state${NC}"
        return 0
    else
        echo -e "${RED}✗ Stack $STACK_NAME not found or in invalid state: $STACK_STATUS${NC}"
        return 1
    fi
}

# Function to get stack outputs
get_stack_outputs() {
    echo -e "${BLUE}2. Retrieving stack outputs...${NC}"
    
    API_URL=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --query 'Stacks[0].Outputs[?OutputKey==`OrderProcessingAPIUrl`].OutputValue' \
        --output text 2>/dev/null)
    
    ORDERS_TABLE=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --query 'Stacks[0].Outputs[?OutputKey==`OrdersTableName`].OutputValue' \
        --output text 2>/dev/null)
    
    EVENT_BUS=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --query 'Stacks[0].Outputs[?OutputKey==`EventBusName`].OutputValue' \
        --output text 2>/dev/null)
    
    if [ -n "$API_URL" ] && [ "$API_URL" != "None" ]; then
        echo -e "${GREEN}✓ API Gateway URL: $API_URL${NC}"
    else
        echo -e "${RED}✗ Could not retrieve API Gateway URL${NC}"
        return 1
    fi
    
    if [ -n "$ORDERS_TABLE" ] && [ "$ORDERS_TABLE" != "None" ]; then
        echo -e "${GREEN}✓ Orders Table: $ORDERS_TABLE${NC}"
    else
        echo -e "${RED}✗ Could not retrieve Orders table name${NC}"
        return 1
    fi
    
    if [ -n "$EVENT_BUS" ] && [ "$EVENT_BUS" != "None" ]; then
        echo -e "${GREEN}✓ Event Bus: $EVENT_BUS${NC}"
    else
        echo -e "${RED}✗ Could not retrieve Event Bus name${NC}"
        return 1
    fi
}

# Function to check Lambda functions
check_lambda_functions() {
    echo -e "${BLUE}3. Checking Lambda functions...${NC}"
    
    local functions=(
        "$PROJECT_NAME-$ENVIRONMENT-order-handler"
        "$PROJECT_NAME-$ENVIRONMENT-inventory-handler"
        "$PROJECT_NAME-$ENVIRONMENT-payment-handler"
        "$PROJECT_NAME-$ENVIRONMENT-inventory-consumer"
        "$PROJECT_NAME-$ENVIRONMENT-payment-consumer"
        "$PROJECT_NAME-$ENVIRONMENT-notification-consumer"
        "$PROJECT_NAME-$ENVIRONMENT-authorizer"
    )
    
    local all_functions_ok=true
    
    for func in "${functions[@]}"; do
        local status=$(aws lambda get-function \
            --function-name "$func" \
            --query 'Configuration.State' \
            --output text 2>/dev/null || echo "NOT_FOUND")
        
        if [ "$status" = "Active" ]; then
            echo -e "${GREEN}✓ $func is active${NC}"
        else
            echo -e "${RED}✗ $func is not active or not found (status: $status)${NC}"
            all_functions_ok=false
        fi
    done
    
    return $all_functions_ok
}

# Function to check DynamoDB tables
check_dynamodb_tables() {
    echo -e "${BLUE}4. Checking DynamoDB tables...${NC}"
    
    local tables=(
        "$PROJECT_NAME-$ENVIRONMENT-Orders"
        "$PROJECT_NAME-$ENVIRONMENT-Inventory"
        "$PROJECT_NAME-$ENVIRONMENT-Payments"
        "$PROJECT_NAME-$ENVIRONMENT-IdempotencyKeys"
    )
    
    local all_tables_ok=true
    
    for table in "${tables[@]}"; do
        local status=$(aws dynamodb describe-table \
            --table-name "$table" \
            --query 'Table.TableStatus' \
            --output text 2>/dev/null || echo "NOT_FOUND")
        
        if [ "$status" = "ACTIVE" ]; then
            echo -e "${GREEN}✓ $table is active${NC}"
        else
            echo -e "${RED}✗ $table is not active or not found (status: $status)${NC}"
            all_tables_ok=false
        fi
    done
    
    return $all_tables_ok
}

# Function to check EventBridge
check_eventbridge() {
    echo -e "${BLUE}5. Checking EventBridge configuration...${NC}"
    
    local bus_exists=$(aws events describe-event-bus \
        --name "$EVENT_BUS" 2>/dev/null || echo "NOT_FOUND")
    
    if [ "$bus_exists" != "NOT_FOUND" ]; then
        echo -e "${GREEN}✓ Event bus $EVENT_BUS exists${NC}"
    else
        echo -e "${RED}✗ Event bus $EVENT_BUS not found${NC}"
        return 1
    fi
    
    # Check for rules
    local rules=$(aws events list-rules \
        --event-bus-name "$EVENT_BUS" \
        --query 'Rules[].Name' \
        --output text 2>/dev/null || echo "")
    
    if [ -n "$rules" ]; then
        echo -e "${GREEN}✓ EventBridge rules found: $rules${NC}"
    else
        echo -e "${YELLOW}⚠ No EventBridge rules found${NC}"
    fi
}

# Function to test API endpoints
test_api_endpoints() {
    echo -e "${BLUE}6. Testing API endpoints...${NC}"
    
    # Test order placement
    echo -e "${BLUE}   Testing order placement...${NC}"
    local order_response=$(curl -s -w "%{http_code}" -X POST "${API_URL}orders" \
        -H "Content-Type: application/json" \
        -H "Authorization: Basic YWRtaW46" \
        -d '{
            "customerId": "validation-test",
            "items": [
                {"vendorId": "test-vendor", "productId": "test-product", "quantity": 1}
            ]
        }' 2>/dev/null || echo "ERROR000")
    
    local order_http_code="${order_response: -3}"
    local order_body="${order_response%???}"
    
    if [ "$order_http_code" = "201" ] || [ "$order_http_code" = "200" ]; then
        echo -e "${GREEN}✓ Order placement API working (HTTP $order_http_code)${NC}"
        echo -e "${BLUE}   Response: $order_body${NC}"
    else
        echo -e "${RED}✗ Order placement API failed (HTTP $order_http_code)${NC}"
        echo -e "${BLUE}   Response: $order_body${NC}"
    fi
    
    # Test inventory update
    echo -e "${BLUE}   Testing inventory update...${NC}"
    local inventory_response=$(curl -s -w "%{http_code}" -X POST "${API_URL}inventory" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer demo-token" \
        -d '{
            "vendorId": "test-vendor",
            "productId": "test-product",
            "quantity": 10
        }' 2>/dev/null || echo "ERROR000")
    
    local inventory_http_code="${inventory_response: -3}"
    local inventory_body="${inventory_response%???}"
    
    if [ "$inventory_http_code" = "200" ]; then
        echo -e "${GREEN}✓ Inventory update API working (HTTP $inventory_http_code)${NC}"
        echo -e "${BLUE}   Response: $inventory_body${NC}"
    else
        echo -e "${RED}✗ Inventory update API failed (HTTP $inventory_http_code)${NC}"
        echo -e "${BLUE}   Response: $inventory_body${NC}"
    fi
    
    # Test payment processing
    echo -e "${BLUE}   Testing payment processing...${NC}"
    local payment_response=$(curl -s -w "%{http_code}" -X POST "${API_URL}payments" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer demo-token" \
        -d '{
            "orderId": "validation-test-order",
            "amount": 100,
            "paymentMethod": "credit_card"
        }' 2>/dev/null || echo "ERROR000")
    
    local payment_http_code="${payment_response: -3}"
    local payment_body="${payment_response%???}"
    
    if [ "$payment_http_code" = "200" ]; then
        echo -e "${GREEN}✓ Payment processing API working (HTTP $payment_http_code)${NC}"
        echo -e "${BLUE}   Response: $payment_body${NC}"
    else
        echo -e "${RED}✗ Payment processing API failed (HTTP $payment_http_code)${NC}"
        echo -e "${BLUE}   Response: $payment_body${NC}"
    fi
}

# Function to check CloudWatch logs
check_cloudwatch_logs() {
    echo -e "${BLUE}7. Checking CloudWatch logs...${NC}"
    
    local log_groups=$(aws logs describe-log-groups \
        --log-group-name-prefix "/aws/lambda/$PROJECT_NAME-$ENVIRONMENT" \
        --query 'logGroups[].logGroupName' \
        --output text 2>/dev/null || echo "")
    
    if [ -n "$log_groups" ]; then
        echo -e "${GREEN}✓ CloudWatch log groups found:${NC}"
        for group in $log_groups; do
            echo -e "${GREEN}   - $group${NC}"
        done
    else
        echo -e "${YELLOW}⚠ No CloudWatch log groups found${NC}"
    fi
}

# Function to check recent errors
check_recent_errors() {
    echo -e "${BLUE}8. Checking for recent errors...${NC}"
    
    local error_count=$(aws logs filter-log-events \
        --log-group-name "/aws/lambda/$PROJECT_NAME-$ENVIRONMENT-order-handler" \
        --start-time $(date -d '1 hour ago' +%s)000 \
        --filter-pattern "ERROR" \
        --query 'length(events)' \
        --output text 2>/dev/null || echo "0")
    
    if [ "$error_count" = "0" ]; then
        echo -e "${GREEN}✓ No recent errors found in logs${NC}"
    else
        echo -e "${YELLOW}⚠ Found $error_count recent errors in logs${NC}"
    fi
}

# Main validation function
run_validation() {
    local validation_passed=true
    
    check_stack_exists || validation_passed=false
    get_stack_outputs || validation_passed=false
    check_lambda_functions || validation_passed=false
    check_dynamodb_tables || validation_passed=false
    check_eventbridge || validation_passed=false
    test_api_endpoints || validation_passed=false
    check_cloudwatch_logs || validation_passed=false
    check_recent_errors || validation_passed=false
    
    echo ""
    echo -e "${BLUE}=== Validation Summary ===${NC}"
    
    if [ "$validation_passed" = true ]; then
        echo -e "${GREEN}✓ All validation checks passed!${NC}"
        echo -e "${GREEN}✓ The Order Processing System is deployed and functioning correctly.${NC}"
        echo ""
        echo -e "${BLUE}Next Steps:${NC}"
        echo -e "${BLUE}- Create user credentials in AWS Secrets Manager${NC}"
        echo -e "${BLUE}- Set up monitoring and alerts${NC}"
        echo -e "${BLUE}- Configure custom domain (if needed)${NC}"
        echo -e "${BLUE}- Run load tests${NC}"
        return 0
    else
        echo -e "${RED}✗ Some validation checks failed.${NC}"
        echo -e "${RED}✗ Please review the errors above and fix them.${NC}"
        echo ""
        echo -e "${BLUE}Common fixes:${NC}"
        echo -e "${BLUE}- Wait a few minutes for resources to fully initialize${NC}"
        echo -e "${BLUE}- Check CloudFormation events: aws cloudformation describe-stack-events --stack-name $STACK_NAME${NC}"
        echo -e "${BLUE}- Check Lambda function logs: sam logs -n OrderHandler --stack-name $STACK_NAME${NC}"
        return 1
    fi
}

# Run the validation
run_validation
