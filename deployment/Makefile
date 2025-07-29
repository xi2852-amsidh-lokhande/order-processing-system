# Order Processing System - Makefile for SAM deployment
# Usage: make [target] ENV=<environment>

# Default values
PROJECT_NAME ?= order-processing-system
ENV ?= dev
REGION ?= us-east-1
STACK_NAME = $(PROJECT_NAME)-$(ENV)

# Colors for output
GREEN = \033[0;32m
YELLOW = \033[1;33m
RED = \033[0;31m
BLUE = \033[0;34m
NC = \033[0m # No Color

.PHONY: help check-prereqs validate build deploy deploy-guided test logs local cleanup outputs

# Default target
help: ## Show this help message
	@echo "$(GREEN)Order Processing System - SAM Deployment$(NC)"
	@echo ""
	@echo "$(YELLOW)Usage:$(NC) make [target] ENV=<environment>"
	@echo ""
	@echo "$(YELLOW)Available targets:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(YELLOW)Examples:$(NC)"
	@echo "  make deploy                    # Deploy to dev environment"
	@echo "  make deploy ENV=prod           # Deploy to production"
	@echo "  make test ENV=staging          # Test staging environment"
	@echo "  make logs FUNCTION=OrderHandler ENV=dev"
	@echo ""
	@echo "$(YELLOW)Available environments:$(NC) dev (default), staging, prod"

check-prereqs: ## Check if all prerequisites are installed
	@echo "$(BLUE)Checking prerequisites...$(NC)"
	@command -v aws >/dev/null 2>&1 || { echo "$(RED)ERROR: AWS CLI is required but not installed.$(NC)" >&2; exit 1; }
	@command -v sam >/dev/null 2>&1 || { echo "$(RED)ERROR: SAM CLI is required but not installed.$(NC)" >&2; exit 1; }
	@command -v python >/dev/null 2>&1 || command -v python3 >/dev/null 2>&1 || { echo "$(RED)ERROR: Python is required but not installed.$(NC)" >&2; exit 1; }
	@aws sts get-caller-identity >/dev/null 2>&1 || { echo "$(RED)ERROR: AWS credentials not configured.$(NC)" >&2; exit 1; }
	@echo "$(GREEN)✓ All prerequisites met$(NC)"

validate: check-prereqs ## Validate the SAM template
	@echo "$(BLUE)Validating SAM template...$(NC)"
	@cd deployment && sam validate --template template.yaml
	@echo "$(GREEN)✓ Template validation successful$(NC)"

build: validate ## Build the SAM application
	@echo "$(BLUE)Building SAM application...$(NC)"
	@cd deployment && sam build --template template.yaml --cached --parallel
	@echo "$(GREEN)✓ Build successful$(NC)"

deploy: build ## Deploy to specified environment
	@echo "$(BLUE)Deploying to environment: $(ENV)$(NC)"
	@cd deployment && \
	if [ "$(ENV)" = "dev" ]; then \
		sam deploy; \
	else \
		sam deploy --config-env $(ENV); \
	fi
	@echo "$(GREEN)✓ Deployment successful$(NC)"
	@$(MAKE) outputs ENV=$(ENV)

deploy-guided: build ## Deploy with guided prompts
	@echo "$(BLUE)Running guided deployment...$(NC)"
	@cd deployment && sam deploy --guided
	@echo "$(GREEN)✓ Guided deployment completed$(NC)"

test: ## Test the deployed API
	@echo "$(BLUE)Testing deployment in $(ENV) environment...$(NC)"
	@API_URL=$$(aws cloudformation describe-stacks \
		--stack-name $(STACK_NAME) \
		--query 'Stacks[0].Outputs[?OutputKey==`OrderProcessingAPIUrl`].OutputValue' \
		--output text 2>/dev/null); \
	if [ -n "$$API_URL" ] && [ "$$API_URL" != "None" ]; then \
		echo "$(BLUE)Testing API endpoint: $${API_URL}orders$(NC)"; \
		RESPONSE=$$(curl -s -w "%{http_code}" -X POST "$${API_URL}orders" \
			-H "Content-Type: application/json" \
			-H "Authorization: Basic YWRtaW46" \
			-d '{"customerId":"test-customer","items":[{"vendorId":"test-vendor","productId":"test-product","quantity":1}]}'); \
		HTTP_CODE=$${RESPONSE: -3}; \
		BODY=$${RESPONSE%???}; \
		if [ "$$HTTP_CODE" = "201" ] || [ "$$HTTP_CODE" = "200" ]; then \
			echo "$(GREEN)✓ API test successful (HTTP $$HTTP_CODE)$(NC)"; \
			echo "$(BLUE)Response: $$BODY$(NC)"; \
		else \
			echo "$(YELLOW)⚠ API test returned HTTP $$HTTP_CODE$(NC)"; \
			echo "$(BLUE)Response: $$BODY$(NC)"; \
		fi; \
	else \
		echo "$(RED)ERROR: Could not get API URL from stack outputs$(NC)"; \
	fi

logs: ## Show logs for a Lambda function (usage: make logs FUNCTION=OrderHandler ENV=dev)
	@FUNCTION_NAME ?= OrderHandler
	@echo "$(BLUE)Showing logs for $(FUNCTION_NAME) in $(ENV) environment...$(NC)"
	@cd deployment && sam logs -n $(FUNCTION_NAME) --stack-name $(STACK_NAME) --tail

local: build ## Start local API server
	@echo "$(BLUE)Starting local API server...$(NC)"
	@cd deployment && sam local start-api --template template.yaml --port 3000

local-invoke: build ## Invoke a Lambda function locally
	@FUNCTION_NAME ?= OrderHandler
	@EVENT_FILE ?= events/test-order-event.json
	@echo "$(BLUE)Invoking $(FUNCTION_NAME) locally with $(EVENT_FILE)...$(NC)"
	@cd deployment && sam local invoke $(FUNCTION_NAME) --event $(EVENT_FILE)

cleanup: ## Delete the CloudFormation stack
	@echo "$(YELLOW)WARNING: This will delete the entire stack: $(STACK_NAME)$(NC)"
	@read -p "Are you sure? (y/N): " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		echo "$(BLUE)Deleting stack: $(STACK_NAME)$(NC)"; \
		aws cloudformation delete-stack --stack-name $(STACK_NAME); \
		echo "$(GREEN)✓ Stack deletion initiated$(NC)"; \
	else \
		echo "$(BLUE)Cleanup cancelled$(NC)"; \
	fi

outputs: ## Show CloudFormation stack outputs
	@echo "$(BLUE)Getting stack outputs for $(ENV) environment...$(NC)"
	@API_URL=$$(aws cloudformation describe-stacks \
		--stack-name $(STACK_NAME) \
		--query 'Stacks[0].Outputs[?OutputKey==`OrderProcessingAPIUrl`].OutputValue' \
		--output text 2>/dev/null); \
	if [ -n "$$API_URL" ] && [ "$$API_URL" != "None" ]; then \
		echo "$(GREEN)API Gateway URL: $$API_URL$(NC)"; \
	fi; \
	ORDERS_TABLE=$$(aws cloudformation describe-stacks \
		--stack-name $(STACK_NAME) \
		--query 'Stacks[0].Outputs[?OutputKey==`OrdersTableName`].OutputValue' \
		--output text 2>/dev/null); \
	if [ -n "$$ORDERS_TABLE" ] && [ "$$ORDERS_TABLE" != "None" ]; then \
		echo "$(GREEN)Orders Table: $$ORDERS_TABLE$(NC)"; \
	fi; \
	EVENT_BUS=$$(aws cloudformation describe-stacks \
		--stack-name $(STACK_NAME) \
		--query 'Stacks[0].Outputs[?OutputKey==`EventBusName`].OutputValue' \
		--output text 2>/dev/null); \
	if [ -n "$$EVENT_BUS" ] && [ "$$EVENT_BUS" != "None" ]; then \
		echo "$(GREEN)Event Bus: $$EVENT_BUS$(NC)"; \
	fi

status: ## Show stack status
	@echo "$(BLUE)Stack status for $(STACK_NAME):$(NC)"
	@aws cloudformation describe-stacks \
		--stack-name $(STACK_NAME) \
		--query 'Stacks[0].StackStatus' \
		--output text 2>/dev/null || echo "$(YELLOW)Stack not found$(NC)"

describe: ## Describe stack resources
	@echo "$(BLUE)Stack resources for $(STACK_NAME):$(NC)"
	@aws cloudformation describe-stack-resources \
		--stack-name $(STACK_NAME) \
		--query 'StackResources[].{Type:ResourceType,Status:ResourceStatus,LogicalId:LogicalResourceId}' \
		--output table 2>/dev/null || echo "$(YELLOW)Stack not found$(NC)"

events: ## Show recent stack events
	@echo "$(BLUE)Recent events for $(STACK_NAME):$(NC)"
	@aws cloudformation describe-stack-events \
		--stack-name $(STACK_NAME) \
		--query 'StackEvents[0:10].{Time:Timestamp,Status:ResourceStatus,Type:ResourceType,Reason:ResourceStatusReason}' \
		--output table 2>/dev/null || echo "$(YELLOW)Stack not found$(NC)"

# Development shortcuts
dev-deploy: ## Quick deploy to dev environment
	@$(MAKE) deploy ENV=dev

dev-test: ## Quick test of dev environment
	@$(MAKE) test ENV=dev

dev-logs: ## Show dev environment logs
	@$(MAKE) logs ENV=dev

prod-deploy: ## Deploy to production (with confirmation)
	@echo "$(YELLOW)WARNING: Deploying to PRODUCTION environment$(NC)"
	@read -p "Are you sure? (y/N): " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		$(MAKE) deploy ENV=prod; \
	else \
		echo "$(BLUE)Production deployment cancelled$(NC)"; \
	fi

# Quick development workflow
dev-full: ## Full development workflow (build, deploy, test)
	@$(MAKE) build
	@$(MAKE) deploy ENV=dev
	@$(MAKE) test ENV=dev
	@$(MAKE) outputs ENV=dev

# Package for deployment to other accounts/regions
package: build ## Package the application for deployment
	@BUCKET_NAME ?= $(PROJECT_NAME)-sam-$(shell date +%s)
	@echo "$(BLUE)Packaging application...$(NC)"
	@cd deployment && sam package \
		--s3-bucket $(BUCKET_NAME) \
		--s3-prefix $(PROJECT_NAME) \
		--output-template-file packaged-template.yaml
	@echo "$(GREEN)✓ Application packaged to packaged-template.yaml$(NC)"

install-deps: ## Install Python dependencies locally
	@echo "$(BLUE)Installing Python dependencies...$(NC)"
	@pip install -r requirements.txt
	@echo "$(GREEN)✓ Dependencies installed$(NC)"
