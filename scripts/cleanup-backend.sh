#!/bin/bash

# Cleanup West of Haunted House backend resources
# This script removes Lambda, DynamoDB, and API Gateway resources
# but PRESERVES the Amplify app for future deployments

set -e  # Exit on error

echo "=========================================="
echo "Cleaning up Backend Resources"
echo "=========================================="
echo ""
echo "⚠️  WARNING: This will delete backend resources but preserve the Amplify app"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
AWS_PROFILE="${AWS_PROFILE:-amplify-deploy}"
AWS_REGION="${AWS_REGION:-us-east-1}"
DRY_RUN="${DRY_RUN:-false}"
FORCE="${FORCE:-false}"

# Required tags for resource identification
PROJECT_TAG="west-of-haunted-house"
MANAGED_BY_TAG="vedfolnir"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --profile)
            AWS_PROFILE="$2"
            shift 2
            ;;
        --region)
            AWS_REGION="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --force)
            FORCE=true
            shift
            ;;
        --help)
            echo "Usage: ./scripts/cleanup-backend.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --profile PROFILE    AWS CLI profile to use (default: amplify-deploy)"
            echo "  --region REGION      AWS region (default: us-east-1)"
            echo "  --dry-run            Show what would be deleted without deleting"
            echo "  --force              Skip confirmation prompt"
            echo "  --help               Show this help message"
            echo ""
            echo "This script removes:"
            echo "  - Lambda functions"
            echo "  - DynamoDB tables"
            echo "  - API Gateway APIs"
            echo "  - CloudWatch log groups"
            echo "  - IAM roles (Lambda execution roles only)"
            echo ""
            echo "This script PRESERVES:"
            echo "  - Amplify app and hosting"
            echo "  - GitHub connection"
            echo "  - Amplify service role"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Run with --help for usage information"
            exit 1
            ;;
    esac
done

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo -e "${RED}Error: AWS CLI is not installed${NC}"
    exit 1
fi

# Verify AWS credentials
echo -e "${YELLOW}Verifying AWS credentials...${NC}"
if aws sts get-caller-identity --profile "$AWS_PROFILE" --region "$AWS_REGION" &> /dev/null; then
    ACCOUNT_ID=$(aws sts get-caller-identity --profile "$AWS_PROFILE" --query Account --output text)
    echo -e "${GREEN}✓ AWS credentials verified${NC}"
    echo "  Account: $ACCOUNT_ID"
    echo "  Region: $AWS_REGION"
else
    echo -e "${RED}Error: AWS credentials not configured${NC}"
    exit 1
fi

# Function to check if resource has required tags
has_required_tags() {
    local tags="$1"
    echo "$tags" | jq -e ".Project == \"$PROJECT_TAG\" and .ManagedBy == \"$MANAGED_BY_TAG\"" > /dev/null 2>&1
}

# Discover resources
echo ""
echo -e "${BLUE}Discovering backend resources...${NC}"

# Find Lambda functions
echo -e "${YELLOW}Finding Lambda functions...${NC}"
LAMBDA_FUNCTIONS=$(aws lambda list-functions --region "$AWS_REGION" --profile "$AWS_PROFILE" \
    --query "Functions[?Tags.Project=='$PROJECT_TAG' && Tags.ManagedBy=='$MANAGED_BY_TAG'].FunctionName" \
    --output text 2>/dev/null || echo "")

if [ -n "$LAMBDA_FUNCTIONS" ]; then
    echo -e "${GREEN}Found Lambda functions:${NC}"
    for func in $LAMBDA_FUNCTIONS; do
        echo "  - $func"
    done
else
    echo "  No Lambda functions found"
fi

# Find DynamoDB tables
echo -e "${YELLOW}Finding DynamoDB tables...${NC}"
ALL_TABLES=$(aws dynamodb list-tables --region "$AWS_REGION" --profile "$AWS_PROFILE" \
    --query "TableNames" --output text 2>/dev/null || echo "")

DYNAMODB_TABLES=""
for table in $ALL_TABLES; do
    TAGS=$(aws dynamodb list-tags-of-resource --region "$AWS_REGION" --profile "$AWS_PROFILE" \
        --resource-arn "arn:aws:dynamodb:$AWS_REGION:$ACCOUNT_ID:table/$table" \
        --query "Tags" --output json 2>/dev/null || echo "[]")
    
    PROJECT=$(echo "$TAGS" | jq -r '.[] | select(.Key=="Project") | .Value')
    MANAGED_BY=$(echo "$TAGS" | jq -r '.[] | select(.Key=="ManagedBy") | .Value')
    
    if [ "$PROJECT" = "$PROJECT_TAG" ] && [ "$MANAGED_BY" = "$MANAGED_BY_TAG" ]; then
        DYNAMODB_TABLES="$DYNAMODB_TABLES $table"
    fi
done

if [ -n "$DYNAMODB_TABLES" ]; then
    echo -e "${GREEN}Found DynamoDB tables:${NC}"
    for table in $DYNAMODB_TABLES; do
        echo "  - $table"
    done
else
    echo "  No DynamoDB tables found"
fi

# Find API Gateway APIs
echo -e "${YELLOW}Finding API Gateway APIs...${NC}"
ALL_APIS=$(aws apigateway get-rest-apis --region "$AWS_REGION" --profile "$AWS_PROFILE" \
    --query "items[].id" --output text 2>/dev/null || echo "")

API_GATEWAY_APIS=""
for api_id in $ALL_APIS; do
    TAGS=$(aws apigateway get-tags --region "$AWS_REGION" --profile "$AWS_PROFILE" \
        --resource-arn "arn:aws:apigateway:$AWS_REGION::/restapis/$api_id" \
        --query "tags" --output json 2>/dev/null || echo "{}")
    
    PROJECT=$(echo "$TAGS" | jq -r '.Project // empty')
    MANAGED_BY=$(echo "$TAGS" | jq -r '.ManagedBy // empty')
    
    if [ "$PROJECT" = "$PROJECT_TAG" ] && [ "$MANAGED_BY" = "$MANAGED_BY_TAG" ]; then
        API_NAME=$(aws apigateway get-rest-api --region "$AWS_REGION" --profile "$AWS_PROFILE" \
            --rest-api-id "$api_id" --query "name" --output text)
        API_GATEWAY_APIS="$API_GATEWAY_APIS $api_id:$API_NAME"
    fi
done

if [ -n "$API_GATEWAY_APIS" ]; then
    echo -e "${GREEN}Found API Gateway APIs:${NC}"
    for api in $API_GATEWAY_APIS; do
        api_id="${api%%:*}"
        api_name="${api##*:}"
        echo "  - $api_name ($api_id)"
    done
else
    echo "  No API Gateway APIs found"
fi

# Check if any resources found
if [ -z "$LAMBDA_FUNCTIONS" ] && [ -z "$DYNAMODB_TABLES" ] && [ -z "$API_GATEWAY_APIS" ]; then
    echo ""
    echo -e "${YELLOW}No backend resources found to clean up${NC}"
    exit 0
fi

# Dry run mode
if [ "$DRY_RUN" = true ]; then
    echo ""
    echo -e "${YELLOW}DRY RUN MODE - No resources will be deleted${NC}"
    echo ""
    echo "The following resources would be deleted:"
    [ -n "$LAMBDA_FUNCTIONS" ] && echo "  - Lambda functions: $(echo $LAMBDA_FUNCTIONS | wc -w)"
    [ -n "$DYNAMODB_TABLES" ] && echo "  - DynamoDB tables: $(echo $DYNAMODB_TABLES | wc -w)"
    [ -n "$API_GATEWAY_APIS" ] && echo "  - API Gateway APIs: $(echo $API_GATEWAY_APIS | wc -w)"
    echo ""
    echo "Run without --dry-run to perform cleanup"
    exit 0
fi

# Confirmation prompt
if [ "$FORCE" != true ]; then
    echo ""
    echo -e "${RED}⚠️  WARNING: This will permanently delete the resources listed above${NC}"
    echo -e "${GREEN}The Amplify app will be preserved for future deployments${NC}"
    echo ""
    read -p "Are you sure you want to continue? (yes/no): " -r
    echo
    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        echo "Cleanup cancelled"
        exit 0
    fi
fi

# Delete resources in correct order
echo ""
echo -e "${BLUE}Starting cleanup...${NC}"

# 1. Delete API Gateway APIs
if [ -n "$API_GATEWAY_APIS" ]; then
    echo ""
    echo -e "${YELLOW}Deleting API Gateway APIs...${NC}"
    for api in $API_GATEWAY_APIS; do
        api_id="${api%%:*}"
        api_name="${api##*:}"
        echo "  Deleting $api_name..."
        aws apigateway delete-rest-api --region "$AWS_REGION" --profile "$AWS_PROFILE" \
            --rest-api-id "$api_id" 2>/dev/null || echo "    Failed to delete"
    done
    echo -e "${GREEN}✓ API Gateway APIs deleted${NC}"
fi

# 2. Delete Lambda functions
if [ -n "$LAMBDA_FUNCTIONS" ]; then
    echo ""
    echo -e "${YELLOW}Deleting Lambda functions...${NC}"
    for func in $LAMBDA_FUNCTIONS; do
        echo "  Deleting $func..."
        aws lambda delete-function --region "$AWS_REGION" --profile "$AWS_PROFILE" \
            --function-name "$func" 2>/dev/null || echo "    Failed to delete"
        
        # Delete associated log group
        LOG_GROUP="/aws/lambda/$func"
        aws logs delete-log-group --region "$AWS_REGION" --profile "$AWS_PROFILE" \
            --log-group-name "$LOG_GROUP" 2>/dev/null || true
    done
    echo -e "${GREEN}✓ Lambda functions deleted${NC}"
fi

# 3. Delete DynamoDB tables
if [ -n "$DYNAMODB_TABLES" ]; then
    echo ""
    echo -e "${YELLOW}Deleting DynamoDB tables...${NC}"
    for table in $DYNAMODB_TABLES; do
        echo "  Deleting $table..."
        aws dynamodb delete-table --region "$AWS_REGION" --profile "$AWS_PROFILE" \
            --table-name "$table" 2>/dev/null || echo "    Failed to delete"
    done
    echo -e "${GREEN}✓ DynamoDB tables deleted${NC}"
fi

# 4. Clean up Lambda execution roles (but not Amplify service role)
echo ""
echo -e "${YELLOW}Cleaning up Lambda execution roles...${NC}"
LAMBDA_ROLES=$(aws iam list-roles --profile "$AWS_PROFILE" \
    --query "Roles[?contains(RoleName, 'gameHandler') || contains(RoleName, 'game-handler')].RoleName" \
    --output text 2>/dev/null || echo "")

if [ -n "$LAMBDA_ROLES" ]; then
    for role in $LAMBDA_ROLES; do
        # Skip Amplify service roles
        if [[ "$role" == *"amplify"* ]] && [[ "$role" != *"gameHandler"* ]] && [[ "$role" != *"game-handler"* ]]; then
            echo "  Skipping Amplify service role: $role"
            continue
        fi
        
        echo "  Deleting role: $role"
        
        # Detach managed policies
        ATTACHED_POLICIES=$(aws iam list-attached-role-policies --profile "$AWS_PROFILE" \
            --role-name "$role" --query "AttachedPolicies[].PolicyArn" --output text 2>/dev/null || echo "")
        for policy in $ATTACHED_POLICIES; do
            aws iam detach-role-policy --profile "$AWS_PROFILE" \
                --role-name "$role" --policy-arn "$policy" 2>/dev/null || true
        done
        
        # Delete inline policies
        INLINE_POLICIES=$(aws iam list-role-policies --profile "$AWS_PROFILE" \
            --role-name "$role" --query "PolicyNames" --output text 2>/dev/null || echo "")
        for policy in $INLINE_POLICIES; do
            aws iam delete-role-policy --profile "$AWS_PROFILE" \
                --role-name "$role" --policy-name "$policy" 2>/dev/null || true
        done
        
        # Delete role
        aws iam delete-role --profile "$AWS_PROFILE" --role-name "$role" 2>/dev/null || echo "    Failed to delete"
    done
    echo -e "${GREEN}✓ Lambda execution roles deleted${NC}"
else
    echo "  No Lambda execution roles found"
fi

echo ""
echo -e "${GREEN}=========================================="
echo "Cleanup complete!"
echo "==========================================${NC}"
echo ""
echo -e "${GREEN}✓ Backend resources removed${NC}"
echo -e "${GREEN}✓ Amplify app preserved${NC}"
echo ""
echo "The Amplify app is ready for new deployments."
echo "To redeploy, run: ./scripts/deploy-gen2.sh"
