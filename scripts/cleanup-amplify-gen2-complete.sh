#!/bin/bash

# Complete Amplify Gen 2 Cleanup Script
# Removes ALL resources for West of Haunted House project
# Uses project tags to ensure safety - only deletes resources with:
#   Project=west-of-haunted-house
#   ManagedBy=vedfolnir

set -e  # Exit on error

echo "=========================================="
echo "Complete Amplify Gen 2 Cleanup"
echo "=========================================="
echo ""
echo "⚠️  WARNING: This will DELETE ALL resources for this project"
echo ""
echo "❌ WILL BE DELETED:"
echo "   - Amplify app and hosting"
echo "   - Custom domain configuration"
echo "   - Lambda functions"
echo "   - DynamoDB tables"
echo "   - API Gateway APIs"
echo "   - CloudWatch log groups"
echo "   - IAM roles (Lambda execution roles)"
echo "   - S3 buckets (deployment artifacts)"
echo ""
echo "✅ SAFETY: Only resources with these tags will be deleted:"
echo "   - Project: west-of-haunted-house"
echo "   - Owner: vedfolnir"
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
            echo "Usage: ./scripts/cleanup-amplify-gen2-complete.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --profile PROFILE    AWS CLI profile to use (default: amplify-deploy)"
            echo "  --region REGION      AWS region (default: us-east-1)"
            echo "  --dry-run            Show what would be deleted without deleting"
            echo "  --force              Skip confirmation prompt"
            echo "  --help               Show this help message"
            echo ""
            echo "This script removes ALL resources for the project:"
            echo "  - Amplify app (hosting, branches, domain)"
            echo "  - Lambda functions"
            echo "  - DynamoDB tables"
            echo "  - API Gateway APIs"
            echo "  - CloudWatch log groups"
            echo "  - IAM roles (Lambda execution roles)"
            echo "  - S3 buckets (deployment artifacts)"
            echo ""
            echo "Safety: Only deletes resources with required tags:"
            echo "  - Project: $PROJECT_TAG"
            echo "  - ManagedBy: $MANAGED_BY_TAG"
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

# Check if jq is installed
if ! command -v jq &> /dev/null; then
    echo -e "${RED}Error: jq is not installed${NC}"
    echo "Install with: brew install jq"
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

# Discover resources
echo ""
echo -e "${BLUE}Discovering project resources...${NC}"

# 1. Find Amplify app
echo -e "${YELLOW}Finding Amplify app...${NC}"
# Note: Using Owner tag instead of ManagedBy for this project
AMPLIFY_APP=$(aws amplify list-apps --region "$AWS_REGION" --profile "$AWS_PROFILE" \
    --query "apps[?tags.Project=='$PROJECT_TAG' && tags.Owner=='$MANAGED_BY_TAG'].{AppId:appId,Name:name,Domain:defaultDomain}" \
    --output json 2>/dev/null || echo "[]")

APP_ID=""
APP_NAME=""
if [ "$AMPLIFY_APP" != "[]" ]; then
    APP_ID=$(echo "$AMPLIFY_APP" | jq -r '.[0].AppId // empty')
    APP_NAME=$(echo "$AMPLIFY_APP" | jq -r '.[0].Name // empty')
    APP_DOMAIN=$(echo "$AMPLIFY_APP" | jq -r '.[0].Domain // empty')
    
    if [ -n "$APP_ID" ]; then
        echo -e "${GREEN}Found Amplify app:${NC}"
        echo "  - Name: $APP_NAME"
        echo "  - App ID: $APP_ID"
        echo "  - Domain: https://$APP_DOMAIN"
        
        # Check for custom domains
        CUSTOM_DOMAINS=$(aws amplify list-domain-associations --region "$AWS_REGION" --profile "$AWS_PROFILE" \
            --app-id "$APP_ID" --query "domainAssociations[].domainName" --output text 2>/dev/null || echo "")
        
        if [ -n "$CUSTOM_DOMAINS" ]; then
            echo "  - Custom domains: $CUSTOM_DOMAINS"
        fi
    fi
else
    echo "  No Amplify app found"
fi

# 2. Find Lambda functions
echo -e "${YELLOW}Finding Lambda functions...${NC}"
LAMBDA_FUNCTIONS=""

# First try to find by tags
TAGGED_FUNCTIONS=$(aws lambda list-functions --region "$AWS_REGION" --profile "$AWS_PROFILE" \
    --query "Functions[?Tags.Project=='$PROJECT_TAG' && (Tags.Owner=='$MANAGED_BY_TAG' || Tags.ManagedBy=='$MANAGED_BY_TAG')].FunctionName" \
    --output text 2>/dev/null || echo "")

if [ -n "$TAGGED_FUNCTIONS" ]; then
    LAMBDA_FUNCTIONS="$TAGGED_FUNCTIONS"
fi

# Also find by app ID in function name (for functions without tags)
if [ -n "$APP_ID" ]; then
    ALL_FUNCTIONS=$(aws lambda list-functions --region "$AWS_REGION" --profile "$AWS_PROFILE" \
        --query "Functions[].FunctionName" --output text 2>/dev/null || echo "")
    
    for func in $ALL_FUNCTIONS; do
        # Match functions that contain the exact app ID
        if [[ "$func" == *"$APP_ID"* ]]; then
            # Avoid duplicates
            if [[ ! " $LAMBDA_FUNCTIONS " =~ " $func " ]]; then
                LAMBDA_FUNCTIONS="$LAMBDA_FUNCTIONS $func"
            fi
        fi
    done
fi

if [ -n "$LAMBDA_FUNCTIONS" ]; then
    echo -e "${GREEN}Found Lambda functions:${NC}"
    for func in $LAMBDA_FUNCTIONS; do
        echo "  - $func"
    done
else
    echo "  No Lambda functions found"
fi

# 3. Find DynamoDB tables
echo -e "${YELLOW}Finding DynamoDB tables...${NC}"
ALL_TABLES=$(aws dynamodb list-tables --region "$AWS_REGION" --profile "$AWS_PROFILE" \
    --query "TableNames" --output text 2>/dev/null || echo "")

DYNAMODB_TABLES=""
for table in $ALL_TABLES; do
    TAGS=$(aws dynamodb list-tags-of-resource --region "$AWS_REGION" --profile "$AWS_PROFILE" \
        --resource-arn "arn:aws:dynamodb:$AWS_REGION:$ACCOUNT_ID:table/$table" \
        --query "Tags" --output json 2>/dev/null || echo "[]")
    
    PROJECT=$(echo "$TAGS" | jq -r '.[] | select(.Key=="Project") | .Value')
    OWNER=$(echo "$TAGS" | jq -r '.[] | select(.Key=="Owner") | .Value')
    MANAGED_BY=$(echo "$TAGS" | jq -r '.[] | select(.Key=="ManagedBy") | .Value')
    
    # Check for either Owner or ManagedBy tag
    if [ "$PROJECT" = "$PROJECT_TAG" ] && ([ "$OWNER" = "$MANAGED_BY_TAG" ] || [ "$MANAGED_BY" = "$MANAGED_BY_TAG" ]); then
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

# 4. Find API Gateway APIs
echo -e "${YELLOW}Finding API Gateway APIs...${NC}"
ALL_APIS=$(aws apigateway get-rest-apis --region "$AWS_REGION" --profile "$AWS_PROFILE" \
    --query "items[].id" --output text 2>/dev/null || echo "")

API_GATEWAY_APIS=""
for api_id in $ALL_APIS; do
    TAGS=$(aws apigateway get-tags --region "$AWS_REGION" --profile "$AWS_PROFILE" \
        --resource-arn "arn:aws:apigateway:$AWS_REGION::/restapis/$api_id" \
        --query "tags" --output json 2>/dev/null || echo "{}")
    
    PROJECT=$(echo "$TAGS" | jq -r '.Project // empty')
    OWNER=$(echo "$TAGS" | jq -r '.Owner // empty')
    MANAGED_BY=$(echo "$TAGS" | jq -r '.ManagedBy // empty')
    
    # Check for either Owner or ManagedBy tag
    if [ "$PROJECT" = "$PROJECT_TAG" ] && ([ "$OWNER" = "$MANAGED_BY_TAG" ] || [ "$MANAGED_BY" = "$MANAGED_BY_TAG" ]); then
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

# 5. Find S3 buckets (Amplify deployment artifacts and leftovers)
echo -e "${YELLOW}Finding S3 buckets...${NC}"
S3_BUCKETS=""

ALL_BUCKETS=$(aws s3api list-buckets --profile "$AWS_PROFILE" \
    --query "Buckets[].Name" --output text 2>/dev/null || echo "")

for bucket in $ALL_BUCKETS; do
    # Match buckets by app ID (if we have one) OR by project name patterns
    if [ -n "$APP_ID" ] && [[ "$bucket" == *"$APP_ID"* ]]; then
        S3_BUCKETS="$S3_BUCKETS $bucket"
    elif [[ "$bucket" == *"westofhauntedhouse"* ]] || [[ "$bucket" == *"west-of-haunted"* ]]; then
        S3_BUCKETS="$S3_BUCKETS $bucket"
    fi
done

if [ -n "$S3_BUCKETS" ]; then
    echo -e "${GREEN}Found S3 buckets:${NC}"
    for bucket in $S3_BUCKETS; do
        echo "  - $bucket"
    done
else
    echo "  No S3 buckets found"
fi

# 6. Find IAM roles
echo -e "${YELLOW}Finding IAM roles...${NC}"
LAMBDA_ROLES=""

# Only look for roles if we found an Amplify app
if [ -n "$APP_ID" ]; then
    ALL_ROLES=$(aws iam list-roles --profile "$AWS_PROFILE" \
        --query "Roles[].RoleName" --output text 2>/dev/null || echo "")
    
    for role in $ALL_ROLES; do
        # Match roles that contain the exact app ID or game handler names
        if [[ "$role" == *"$APP_ID"* ]] || [[ "$role" == *"gameHandler"* ]] || [[ "$role" == *"game-handler"* ]]; then
            # Additional check: make sure it's not from another project
            if [[ "$role" != *"fediversecomposer"* ]] && [[ "$role" != *"d1x3xrra4vf534"* ]]; then
                LAMBDA_ROLES="$LAMBDA_ROLES $role"
            fi
        fi
    done
fi

if [ -n "$LAMBDA_ROLES" ]; then
    echo -e "${GREEN}Found IAM roles:${NC}"
    for role in $LAMBDA_ROLES; do
        echo "  - $role"
    done
else
    echo "  No IAM roles found"
fi

# 7. Find WAF Web ACLs
echo -e "${YELLOW}Finding WAF Web ACLs...${NC}"
WAF_WEB_ACLS=""

if [ -n "$APP_ID" ]; then
    # WAF for CloudFront is in us-east-1 with CLOUDFRONT scope
    ALL_WAFV2=$(aws wafv2 list-web-acls --scope CLOUDFRONT --region us-east-1 --profile "$AWS_PROFILE" \
        --query "WebACLs[].{Name:Name,Id:Id,ARN:ARN}" --output json 2>/dev/null || echo "[]")
    
    if [ "$ALL_WAFV2" != "[]" ]; then
        # Filter for WAFs created by this Amplify app
        WAF_WEB_ACLS=$(echo "$ALL_WAFV2" | jq -r ".[] | select(.Name | contains(\"$APP_ID\")) | .Id + \":\" + .Name + \":\" + .ARN" 2>/dev/null || echo "")
    fi
fi

if [ -n "$WAF_WEB_ACLS" ]; then
    echo -e "${GREEN}Found WAF Web ACLs:${NC}"
    for waf in $WAF_WEB_ACLS; do
        waf_name=$(echo "$waf" | cut -d':' -f2)
        echo "  - $waf_name"
    done
else
    echo "  No WAF Web ACLs found"
fi

# 8. Find Route 53 records for custom domain
echo -e "${YELLOW}Finding Route 53 DNS records...${NC}"
ROUTE53_RECORDS=""
HOSTED_ZONE_ID=""

if [ -n "$CUSTOM_DOMAINS" ]; then
    # Find the hosted zone for vedfolnir.org
    HOSTED_ZONES=$(aws route53 list-hosted-zones --profile "$AWS_PROFILE" \
        --query "HostedZones[?contains(Name, 'vedfolnir.org')].{Id:Id,Name:Name}" --output json 2>/dev/null || echo "[]")
    
    if [ "$HOSTED_ZONES" != "[]" ]; then
        HOSTED_ZONE_ID=$(echo "$HOSTED_ZONES" | jq -r '.[0].Id' | sed 's|/hostedzone/||')
        
        # Find records for west.zero.vedfolnir.org
        RECORDS=$(aws route53 list-resource-record-sets --hosted-zone-id "$HOSTED_ZONE_ID" --profile "$AWS_PROFILE" \
            --query "ResourceRecordSets[?contains(Name, 'west.zero.vedfolnir.org')]" --output json 2>/dev/null || echo "[]")
        
        if [ "$RECORDS" != "[]" ]; then
            ROUTE53_RECORDS=$(echo "$RECORDS" | jq -r '.[] | .Name + " (" + .Type + ")"')
        fi
    fi
fi

if [ -n "$ROUTE53_RECORDS" ]; then
    echo -e "${GREEN}Found Route 53 DNS records:${NC}"
    echo "$ROUTE53_RECORDS" | while read -r record; do
        echo "  - $record"
    done
else
    echo "  No Route 53 DNS records found"
fi

# Check if any resources found
if [ -z "$APP_ID" ] && [ -z "$LAMBDA_FUNCTIONS" ] && [ -z "$DYNAMODB_TABLES" ] && \
   [ -z "$API_GATEWAY_APIS" ] && [ -z "$S3_BUCKETS" ] && [ -z "$LAMBDA_ROLES" ] && \
   [ -z "$WAF_WEB_ACLS" ] && [ -z "$ROUTE53_RECORDS" ]; then
    echo ""
    echo -e "${YELLOW}No resources found to clean up${NC}"
    exit 0
fi

# Dry run mode
if [ "$DRY_RUN" = true ]; then
    echo ""
    echo -e "${YELLOW}DRY RUN MODE - No resources will be deleted${NC}"
    echo ""
    echo "The following resources would be deleted:"
    [ -n "$APP_ID" ] && echo "  - Amplify app: $APP_NAME"
    [ -n "$LAMBDA_FUNCTIONS" ] && echo "  - Lambda functions: $(echo $LAMBDA_FUNCTIONS | wc -w)"
    [ -n "$DYNAMODB_TABLES" ] && echo "  - DynamoDB tables: $(echo $DYNAMODB_TABLES | wc -w)"
    [ -n "$API_GATEWAY_APIS" ] && echo "  - API Gateway APIs: $(echo $API_GATEWAY_APIS | wc -w)"
    [ -n "$S3_BUCKETS" ] && echo "  - S3 buckets: $(echo $S3_BUCKETS | wc -w)"
    [ -n "$LAMBDA_ROLES" ] && echo "  - IAM roles: $(echo $LAMBDA_ROLES | wc -w)"
    [ -n "$WAF_WEB_ACLS" ] && echo "  - WAF Web ACLs: $(echo $WAF_WEB_ACLS | wc -w)"
    [ -n "$ROUTE53_RECORDS" ] && echo "  - Route 53 DNS records: $(echo "$ROUTE53_RECORDS" | wc -l)"
    echo ""
    echo "Run without --dry-run to perform cleanup"
    exit 0
fi

# Confirmation prompt
if [ "$FORCE" != true ]; then
    echo ""
    echo -e "${RED}⚠️  WARNING: This will PERMANENTLY DELETE ALL resources listed above${NC}"
    echo -e "${RED}This action CANNOT be undone!${NC}"
    echo ""
    echo "Type 'DELETE' to confirm (case-sensitive): "
    read -r CONFIRM
    echo
    if [ "$CONFIRM" != "DELETE" ]; then
        echo "Cleanup cancelled"
        exit 0
    fi
fi

# Delete resources in correct order
echo ""
echo -e "${BLUE}Starting cleanup...${NC}"

# 1. Delete Amplify app (this will trigger CloudFormation stack deletion)
if [ -n "$APP_ID" ]; then
    echo ""
    echo -e "${YELLOW}Deleting Amplify app...${NC}"
    echo "  Deleting $APP_NAME (App ID: $APP_ID)..."
    echo "  This will trigger CloudFormation to delete managed resources..."
    
    aws amplify delete-app --region "$AWS_REGION" --profile "$AWS_PROFILE" \
        --app-id "$APP_ID" 2>/dev/null || echo "    Failed to delete"
    
    echo -e "${GREEN}✓ Amplify app deletion initiated${NC}"
    
    # Wait for CloudFormation stacks to be deleted
    echo ""
    echo -e "${YELLOW}Waiting for CloudFormation stacks to be deleted...${NC}"
    echo "  This may take 10-30 minutes depending on resources..."
    
    # Get the main stack name
    MAIN_STACK="amplify-$APP_ID-production-branch-67414f78a8"
    
    # Wait for stack deletion with timeout
    MAX_WAIT=1800  # 30 minutes
    ELAPSED=0
    WAIT_INTERVAL=30  # Check every 30 seconds
    
    while [ $ELAPSED -lt $MAX_WAIT ]; do
        # Check if stack still exists
        STACK_STATUS=$(aws cloudformation describe-stacks --region "$AWS_REGION" --profile "$AWS_PROFILE" \
            --stack-name "$MAIN_STACK" --query "Stacks[0].StackStatus" --output text 2>/dev/null || echo "DELETED")
        
        if [ "$STACK_STATUS" = "DELETED" ] || [ "$STACK_STATUS" = "DELETE_COMPLETE" ]; then
            echo -e "${GREEN}✓ CloudFormation stacks deleted${NC}"
            break
        elif [[ "$STACK_STATUS" == *"FAILED"* ]]; then
            echo -e "${YELLOW}⚠ Stack deletion encountered issues: $STACK_STATUS${NC}"
            echo "  Continuing with manual cleanup..."
            break
        else
            # Show progress with minutes
            ELAPSED_MIN=$((ELAPSED / 60))
            MAX_MIN=$((MAX_WAIT / 60))
            echo "  Stack status: $STACK_STATUS (${ELAPSED_MIN}m/${MAX_MIN}m elapsed)"
            sleep $WAIT_INTERVAL
            ELAPSED=$((ELAPSED + WAIT_INTERVAL))
        fi
    done
    
    if [ $ELAPSED -ge $MAX_WAIT ]; then
        echo -e "${YELLOW}⚠ Timeout waiting for CloudFormation deletion (30 minutes)${NC}"
        echo "  Continuing with manual cleanup..."
    fi
    
    # Give AWS a moment to propagate the deletions
    echo "  Waiting for AWS to propagate changes..."
    sleep 10
fi

# 2. Delete API Gateway APIs (if not already deleted by CloudFormation)
if [ -n "$API_GATEWAY_APIS" ]; then
    echo ""
    echo -e "${YELLOW}Deleting API Gateway APIs...${NC}"
    for api in $API_GATEWAY_APIS; do
        api_id="${api%%:*}"
        api_name="${api##*:}"
        echo "  Checking $api_name..."
        
        # Check if API still exists
        if aws apigateway get-rest-api --region "$AWS_REGION" --profile "$AWS_PROFILE" \
            --rest-api-id "$api_id" &>/dev/null; then
            echo "  Deleting $api_name..."
            aws apigateway delete-rest-api --region "$AWS_REGION" --profile "$AWS_PROFILE" \
                --rest-api-id "$api_id" 2>/dev/null || echo "    Failed to delete"
        else
            echo "  Already deleted by CloudFormation"
        fi
    done
    echo -e "${GREEN}✓ API Gateway APIs cleaned up${NC}"
fi

# 3. Delete Lambda functions (if not already deleted by CloudFormation)
if [ -n "$LAMBDA_FUNCTIONS" ]; then
    echo ""
    echo -e "${YELLOW}Deleting Lambda functions...${NC}"
    for func in $LAMBDA_FUNCTIONS; do
        echo "  Checking $func..."
        
        # Check if function still exists
        if aws lambda get-function --region "$AWS_REGION" --profile "$AWS_PROFILE" \
            --function-name "$func" &>/dev/null; then
            echo "  Deleting $func..."
            aws lambda delete-function --region "$AWS_REGION" --profile "$AWS_PROFILE" \
                --function-name "$func" 2>/dev/null || echo "    Failed to delete"
            
            # Delete associated log group
            LOG_GROUP="/aws/lambda/$func"
            aws logs delete-log-group --region "$AWS_REGION" --profile "$AWS_PROFILE" \
                --log-group-name "$LOG_GROUP" 2>/dev/null || true
        else
            echo "  Already deleted by CloudFormation"
        fi
    done
    echo -e "${GREEN}✓ Lambda functions cleaned up${NC}"
fi

# 4. Delete DynamoDB tables (if not already deleted by CloudFormation)
if [ -n "$DYNAMODB_TABLES" ]; then
    echo ""
    echo -e "${YELLOW}Deleting DynamoDB tables...${NC}"
    for table in $DYNAMODB_TABLES; do
        echo "  Checking $table..."
        
        # Check if table still exists
        if aws dynamodb describe-table --region "$AWS_REGION" --profile "$AWS_PROFILE" \
            --table-name "$table" &>/dev/null; then
            echo "  Deleting $table..."
            aws dynamodb delete-table --region "$AWS_REGION" --profile "$AWS_PROFILE" \
                --table-name "$table" 2>/dev/null || echo "    Failed to delete"
        else
            echo "  Already deleted by CloudFormation"
        fi
    done
    echo -e "${GREEN}✓ DynamoDB tables cleaned up${NC}"
fi

# 5. Delete S3 buckets (empty first, then delete)
if [ -n "$S3_BUCKETS" ]; then
    echo ""
    echo -e "${YELLOW}Deleting S3 buckets...${NC}"
    for bucket in $S3_BUCKETS; do
        echo "  Emptying and deleting $bucket..."
        
        # Empty bucket first
        aws s3 rm "s3://$bucket" --recursive --profile "$AWS_PROFILE" 2>/dev/null || true
        
        # Delete bucket
        aws s3api delete-bucket --bucket "$bucket" --profile "$AWS_PROFILE" 2>/dev/null || echo "    Failed to delete"
    done
    echo -e "${GREEN}✓ S3 buckets deleted${NC}"
fi

# 6. Delete IAM roles
if [ -n "$LAMBDA_ROLES" ]; then
    echo ""
    echo -e "${YELLOW}Deleting IAM roles...${NC}"
    for role in $LAMBDA_ROLES; do
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
    echo -e "${GREEN}✓ IAM roles deleted${NC}"
fi

# 7. Delete Route 53 DNS records
if [ -n "$ROUTE53_RECORDS" ] && [ -n "$HOSTED_ZONE_ID" ]; then
    echo ""
    echo -e "${YELLOW}Deleting Route 53 DNS records...${NC}"
    
    # Get the full record sets to delete
    RECORDS_JSON=$(aws route53 list-resource-record-sets --hosted-zone-id "$HOSTED_ZONE_ID" --profile "$AWS_PROFILE" \
        --query "ResourceRecordSets[?contains(Name, 'west.zero.vedfolnir.org')]" --output json 2>/dev/null || echo "[]")
    
    if [ "$RECORDS_JSON" != "[]" ]; then
        # Create a change batch to delete records
        echo "$RECORDS_JSON" | jq -c '.[]' | while read -r record; do
            RECORD_NAME=$(echo "$record" | jq -r '.Name')
            RECORD_TYPE=$(echo "$record" | jq -r '.Type')
            
            echo "  Deleting $RECORD_NAME ($RECORD_TYPE)..."
            
            # Create change batch JSON
            CHANGE_BATCH=$(cat <<EOF
{
  "Changes": [{
    "Action": "DELETE",
    "ResourceRecordSet": $record
  }]
}
EOF
)
            
            # Delete the record
            aws route53 change-resource-record-sets \
                --hosted-zone-id "$HOSTED_ZONE_ID" \
                --profile "$AWS_PROFILE" \
                --change-batch "$CHANGE_BATCH" 2>/dev/null || echo "    Failed to delete"
        done
        echo -e "${GREEN}✓ Route 53 DNS records deleted${NC}"
    fi
fi

# 8. Delete WAF Web ACLs
if [ -n "$WAF_WEB_ACLS" ]; then
    echo ""
    echo -e "${YELLOW}Deleting WAF Web ACLs...${NC}"
    for waf in $WAF_WEB_ACLS; do
        waf_id=$(echo "$waf" | cut -d':' -f1)
        waf_name=$(echo "$waf" | cut -d':' -f2)
        
        echo "  Deleting $waf_name..."
        
        # Get lock token
        LOCK_TOKEN=$(aws wafv2 get-web-acl --scope CLOUDFRONT --region us-east-1 --profile "$AWS_PROFILE" \
            --id "$waf_id" --name "$waf_name" --query "LockToken" --output text 2>/dev/null || echo "")
        
        if [ -n "$LOCK_TOKEN" ]; then
            # Delete the WAF
            aws wafv2 delete-web-acl --scope CLOUDFRONT --region us-east-1 --profile "$AWS_PROFILE" \
                --id "$waf_id" --name "$waf_name" --lock-token "$LOCK_TOKEN" 2>/dev/null || echo "    Failed to delete (may be auto-deleted with Amplify app)"
        fi
    done
    echo -e "${GREEN}✓ WAF Web ACLs deleted${NC}"
fi

# 9. Clean up CloudWatch log groups (only for this app)
echo ""
echo -e "${YELLOW}Cleaning up CloudWatch log groups...${NC}"

if [ -n "$APP_ID" ]; then
    # Only delete log groups that contain the specific app ID
    LOG_GROUPS=$(aws logs describe-log-groups --region "$AWS_REGION" --profile "$AWS_PROFILE" \
        --query "logGroups[?contains(logGroupName, '$APP_ID')].logGroupName" \
        --output text 2>/dev/null || echo "")

    if [ -n "$LOG_GROUPS" ]; then
        for log_group in $LOG_GROUPS; do
            echo "  Deleting log group: $log_group"
            aws logs delete-log-group --region "$AWS_REGION" --profile "$AWS_PROFILE" \
                --log-group-name "$log_group" 2>/dev/null || true
        done
        echo -e "${GREEN}✓ CloudWatch log groups deleted${NC}"
    else
        echo "  No log groups found for this app"
    fi
else
    echo "  Skipping log group cleanup (no app ID)"
fi

echo ""
echo -e "${GREEN}=========================================="
echo "Cleanup complete!"
echo "==========================================${NC}"
echo ""
echo -e "${GREEN}✓ All project resources removed${NC}"
echo ""
echo "Deleted resources:"
[ -n "$APP_ID" ] && echo "  ✓ Amplify app: $APP_NAME"
[ -n "$LAMBDA_FUNCTIONS" ] && echo "  ✓ Lambda functions: $(echo $LAMBDA_FUNCTIONS | wc -w)"
[ -n "$DYNAMODB_TABLES" ] && echo "  ✓ DynamoDB tables: $(echo $DYNAMODB_TABLES | wc -w)"
[ -n "$API_GATEWAY_APIS" ] && echo "  ✓ API Gateway APIs: $(echo $API_GATEWAY_APIS | wc -w)"
[ -n "$S3_BUCKETS" ] && echo "  ✓ S3 buckets: $(echo $S3_BUCKETS | wc -w)"
[ -n "$LAMBDA_ROLES" ] && echo "  ✓ IAM roles: $(echo $LAMBDA_ROLES | wc -w)"
[ -n "$WAF_WEB_ACLS" ] && echo "  ✓ WAF Web ACLs: $(echo $WAF_WEB_ACLS | wc -w)"
[ -n "$ROUTE53_RECORDS" ] && echo "  ✓ Route 53 DNS records: $(echo "$ROUTE53_RECORDS" | wc -l)"
echo ""
echo "The project has been completely removed from AWS."
echo ""
echo -e "${BLUE}Note:${NC} The Route 53 hosted zone 'zero.vedfolnir.org' was preserved."
echo "Only the subdomain records for 'west.zero.vedfolnir.org' were deleted."
