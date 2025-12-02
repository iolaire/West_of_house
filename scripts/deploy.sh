#!/bin/bash

# Deploy West of Haunted House backend to AWS via Amplify CLI
# This script handles the complete deployment process

set -e  # Exit on error

echo "=========================================="
echo "Deploying West of Haunted House Backend"
echo "=========================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
AWS_PROFILE="${AWS_PROFILE:-amplify-deploy}"
SKIP_BUNDLE="${SKIP_BUNDLE:-false}"
SKIP_PACKAGE="${SKIP_PACKAGE:-false}"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --profile)
            AWS_PROFILE="$2"
            shift 2
            ;;
        --skip-bundle)
            SKIP_BUNDLE=true
            shift
            ;;
        --skip-package)
            SKIP_PACKAGE=true
            shift
            ;;
        --help)
            echo "Usage: ./scripts/deploy.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --profile PROFILE    AWS CLI profile to use (default: amplify-deploy)"
            echo "  --skip-bundle        Skip game data bundling step"
            echo "  --skip-package       Skip Lambda packaging step"
            echo "  --help               Show this help message"
            echo ""
            echo "Environment variables:"
            echo "  AWS_PROFILE          AWS CLI profile (default: amplify-deploy)"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Run with --help for usage information"
            exit 1
            ;;
    esac
done

# Check if Amplify CLI is installed
if ! command -v amplify &> /dev/null; then
    echo -e "${RED}Error: Amplify CLI is not installed${NC}"
    echo "Install it with: npm install -g @aws-amplify/cli"
    exit 1
fi

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo -e "${RED}Error: AWS CLI is not installed${NC}"
    echo "Install it from: https://aws.amazon.com/cli/"
    exit 1
fi

# Verify AWS credentials
echo -e "${YELLOW}Verifying AWS credentials...${NC}"
if aws sts get-caller-identity --profile "$AWS_PROFILE" &> /dev/null; then
    ACCOUNT_ID=$(aws sts get-caller-identity --profile "$AWS_PROFILE" --query Account --output text)
    USER_ARN=$(aws sts get-caller-identity --profile "$AWS_PROFILE" --query Arn --output text)
    echo -e "${GREEN}✓ AWS credentials verified${NC}"
    echo "  Account: $ACCOUNT_ID"
    echo "  Identity: $USER_ARN"
else
    echo -e "${RED}Error: AWS credentials not configured for profile: $AWS_PROFILE${NC}"
    echo "Configure credentials with: aws configure --profile $AWS_PROFILE"
    exit 1
fi

# Step 1: Bundle game data
if [ "$SKIP_BUNDLE" = false ]; then
    echo ""
    echo -e "${BLUE}Step 1: Bundling game data...${NC}"
    if [ -f "./scripts/bundle-game-data.sh" ]; then
        chmod +x ./scripts/bundle-game-data.sh
        ./scripts/bundle-game-data.sh
    else
        echo -e "${YELLOW}Warning: bundle-game-data.sh not found, skipping${NC}"
    fi
else
    echo -e "${YELLOW}Skipping game data bundling (--skip-bundle)${NC}"
fi

# Step 2: Package Lambda function
if [ "$SKIP_PACKAGE" = false ]; then
    echo ""
    echo -e "${BLUE}Step 2: Packaging Lambda function...${NC}"
    if [ -f "./scripts/package-lambda.sh" ]; then
        chmod +x ./scripts/package-lambda.sh
        ./scripts/package-lambda.sh
    else
        echo -e "${YELLOW}Warning: package-lambda.sh not found, skipping${NC}"
    fi
else
    echo -e "${YELLOW}Skipping Lambda packaging (--skip-package)${NC}"
fi

# Step 3: Deploy with Amplify
echo ""
echo -e "${BLUE}Step 3: Deploying to AWS with Amplify...${NC}"
echo -e "${YELLOW}This may take several minutes...${NC}"

# Set AWS profile for Amplify
export AWS_PROFILE="$AWS_PROFILE"

# Run amplify push
if amplify push --yes; then
    echo -e "${GREEN}✓ Deployment successful${NC}"
else
    echo -e "${RED}Error: Deployment failed${NC}"
    exit 1
fi

# Step 4: Display deployment information
echo ""
echo -e "${BLUE}Step 4: Retrieving deployment information...${NC}"

# Get API endpoint
if [ -f "src/aws-exports.js" ]; then
    echo -e "${YELLOW}Extracting API endpoint...${NC}"
    API_ENDPOINT=$(grep -o 'endpoint.*https://[^"]*' src/aws-exports.js | cut -d'"' -f2 || echo "Not found")
    if [ "$API_ENDPOINT" != "Not found" ]; then
        echo -e "${GREEN}✓ API Endpoint: $API_ENDPOINT${NC}"
    fi
fi

# Get Lambda function name
LAMBDA_FUNCTION=$(aws lambda list-functions --profile "$AWS_PROFILE" --query "Functions[?contains(FunctionName, 'gameHandler')].FunctionName" --output text 2>/dev/null || echo "")
if [ -n "$LAMBDA_FUNCTION" ]; then
    echo -e "${GREEN}✓ Lambda Function: $LAMBDA_FUNCTION${NC}"
fi

# Get DynamoDB table name
DYNAMODB_TABLE=$(aws dynamodb list-tables --profile "$AWS_PROFILE" --query "TableNames[?contains(@, 'GameSessions')]" --output text 2>/dev/null || echo "")
if [ -n "$DYNAMODB_TABLE" ]; then
    echo -e "${GREEN}✓ DynamoDB Table: $DYNAMODB_TABLE${NC}"
fi

echo ""
echo -e "${GREEN}=========================================="
echo "Deployment complete!"
echo "==========================================${NC}"
echo ""
echo "Next steps:"
echo "  1. Test the API endpoints"
echo "  2. Monitor Lambda logs: aws logs tail /aws/lambda/$LAMBDA_FUNCTION --follow --profile $AWS_PROFILE"
echo "  3. Check DynamoDB table: aws dynamodb describe-table --table-name $DYNAMODB_TABLE --profile $AWS_PROFILE"
echo ""
echo "To update the deployment, run this script again."
