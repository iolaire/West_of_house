#!/bin/bash

# Deploy West of Haunted House backend using Amplify Gen 2
# This script deploys to the existing Amplify app without recreating it

set -e  # Exit on error

echo "=========================================="
echo "Deploying West of Haunted House Gen 2"
echo "=========================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
AWS_PROFILE="${AWS_PROFILE:-amplify-deploy}"
AWS_REGION="${AWS_REGION:-us-east-1}"
DEPLOYMENT_TYPE="${DEPLOYMENT_TYPE:-sandbox}"  # sandbox or pipeline

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
        --type)
            DEPLOYMENT_TYPE="$2"
            shift 2
            ;;
        --help)
            echo "Usage: ./scripts/deploy-gen2.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --profile PROFILE    AWS CLI profile to use (default: amplify-deploy)"
            echo "  --region REGION      AWS region (default: us-east-1)"
            echo "  --type TYPE          Deployment type: sandbox or pipeline (default: sandbox)"
            echo "  --help               Show this help message"
            echo ""
            echo "Deployment types:"
            echo "  sandbox    - Deploy to personal cloud sandbox (for testing)"
            echo "  pipeline   - Deploy via Git push (automatic deployment)"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Run with --help for usage information"
            exit 1
            ;;
    esac
done

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo -e "${RED}Error: Node.js is not installed${NC}"
    echo "Install it from: https://nodejs.org/"
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo -e "${RED}Error: npm is not installed${NC}"
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
if aws sts get-caller-identity --profile "$AWS_PROFILE" --region "$AWS_REGION" &> /dev/null; then
    ACCOUNT_ID=$(aws sts get-caller-identity --profile "$AWS_PROFILE" --query Account --output text)
    USER_ARN=$(aws sts get-caller-identity --profile "$AWS_PROFILE" --query Arn --output text)
    echo -e "${GREEN}✓ AWS credentials verified${NC}"
    echo "  Account: $ACCOUNT_ID"
    echo "  Identity: $USER_ARN"
    echo "  Region: $AWS_REGION"
else
    echo -e "${RED}Error: AWS credentials not configured for profile: $AWS_PROFILE${NC}"
    echo "Configure credentials with: aws configure --profile $AWS_PROFILE"
    exit 1
fi

# Check if amplify directory exists
if [ ! -d "amplify" ]; then
    echo -e "${RED}Error: amplify/ directory not found${NC}"
    echo "Make sure you're in the project root directory"
    exit 1
fi

# Install dependencies if needed
echo ""
echo -e "${BLUE}Step 1: Installing dependencies...${NC}"
cd amplify
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}Installing npm packages...${NC}"
    npm install
else
    echo -e "${GREEN}✓ Dependencies already installed${NC}"
fi
cd ..

# Deploy based on type
echo ""
if [ "$DEPLOYMENT_TYPE" = "sandbox" ]; then
    echo -e "${BLUE}Step 2: Deploying to cloud sandbox...${NC}"
    echo -e "${YELLOW}This creates a personal cloud environment for testing${NC}"
    echo -e "${YELLOW}Press Ctrl+C to stop the sandbox when done${NC}"
    echo ""
    
    export AWS_PROFILE="$AWS_PROFILE"
    cd amplify
    npx ampx sandbox --profile "$AWS_PROFILE"
    cd ..
    
elif [ "$DEPLOYMENT_TYPE" = "pipeline" ]; then
    echo -e "${BLUE}Step 2: Deploying via pipeline...${NC}"
    echo -e "${YELLOW}This requires the Amplify app to be connected to GitHub${NC}"
    echo ""
    
    # Check if there are uncommitted changes
    if ! git diff-index --quiet HEAD --; then
        echo -e "${YELLOW}Warning: You have uncommitted changes${NC}"
        echo "Commit and push your changes to trigger deployment:"
        echo "  git add ."
        echo "  git commit -m 'your message'"
        echo "  git push origin main"
        exit 1
    fi
    
    # Check if we're ahead of origin
    LOCAL=$(git rev-parse @)
    REMOTE=$(git rev-parse @{u} 2>/dev/null || echo "")
    
    if [ "$LOCAL" != "$REMOTE" ]; then
        echo -e "${YELLOW}Pushing to GitHub to trigger deployment...${NC}"
        git push origin main
        echo -e "${GREEN}✓ Code pushed to GitHub${NC}"
        echo ""
        echo "Deployment will start automatically in Amplify Console"
        echo "Monitor progress at: https://console.aws.amazon.com/amplify/home?region=$AWS_REGION"
    else
        echo -e "${GREEN}✓ Code is already up to date with GitHub${NC}"
        echo "No deployment needed"
    fi
else
    echo -e "${RED}Error: Invalid deployment type: $DEPLOYMENT_TYPE${NC}"
    echo "Use 'sandbox' or 'pipeline'"
    exit 1
fi

# Display deployment information
echo ""
echo -e "${BLUE}Step 3: Retrieving deployment information...${NC}"

# Get Amplify app info
AMPLIFY_APP=$(aws amplify list-apps --region "$AWS_REGION" --profile "$AWS_PROFILE" \
    --query "apps[?tags.Project=='west-of-haunted-house'].{AppId:appId,Name:name,Domain:defaultDomain}" \
    --output json 2>/dev/null || echo "[]")

if [ "$AMPLIFY_APP" != "[]" ]; then
    APP_ID=$(echo "$AMPLIFY_APP" | jq -r '.[0].AppId // empty')
    APP_NAME=$(echo "$AMPLIFY_APP" | jq -r '.[0].Name // empty')
    APP_DOMAIN=$(echo "$AMPLIFY_APP" | jq -r '.[0].Domain // empty')
    
    if [ -n "$APP_ID" ]; then
        echo -e "${GREEN}✓ Amplify App: $APP_NAME${NC}"
        echo "  App ID: $APP_ID"
        echo "  Default domain: https://$APP_DOMAIN"
        
        # Check for custom domain
        CUSTOM_DOMAINS=$(aws amplify list-domain-associations --region "$AWS_REGION" --profile "$AWS_PROFILE" \
            --app-id "$APP_ID" --query "domainAssociations[].domainName" --output text 2>/dev/null || echo "")
        
        if [ -n "$CUSTOM_DOMAINS" ]; then
            echo -e "${GREEN}  ✓ Custom domain: $CUSTOM_DOMAINS${NC}"
        fi
    fi
fi

# Get Lambda function
LAMBDA_FUNCTION=$(aws lambda list-functions --region "$AWS_REGION" --profile "$AWS_PROFILE" \
    --query "Functions[?Tags.Project=='west-of-haunted-house'].FunctionName" \
    --output text 2>/dev/null || echo "")

if [ -n "$LAMBDA_FUNCTION" ]; then
    echo -e "${GREEN}✓ Lambda Function: $LAMBDA_FUNCTION${NC}"
fi

# Get DynamoDB table
DYNAMODB_TABLE=$(aws dynamodb list-tables --region "$AWS_REGION" --profile "$AWS_PROFILE" \
    --query "TableNames[?contains(@, 'GameSessions')]" \
    --output text 2>/dev/null || echo "")

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
if [ -n "$LAMBDA_FUNCTION" ]; then
    echo "  2. Monitor Lambda logs: aws logs tail /aws/lambda/$LAMBDA_FUNCTION --follow --profile $AWS_PROFILE"
fi
if [ -n "$DYNAMODB_TABLE" ]; then
    echo "  3. Check DynamoDB table: aws dynamodb describe-table --table-name $DYNAMODB_TABLE --profile $AWS_PROFILE"
fi
echo ""
echo "To update the deployment:"
echo "  - For sandbox: Run this script again"
echo "  - For pipeline: Push changes to GitHub (git push origin main)"
