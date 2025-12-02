#!/bin/bash

###############################################################################
# Gen 2 Deployment Verification Script
#
# This script verifies that all AWS resources for the West of Haunted House
# backend have been deployed correctly with proper configuration.
#
# Checks:
# 1. Lambda function exists with ARM64 architecture
# 2. DynamoDB table exists with TTL enabled
# 3. API Gateway endpoints are accessible
# 4. All resources have required tags (Project, ManagedBy, Environment)
#
# Requirements: 21.1, 21.2, 21.3, 21.4, 24.1, 24.2, 24.3, 24.4
###############################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
PASSED=0
FAILED=0
WARNINGS=0

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Gen 2 Deployment Verification${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

###############################################################################
# Helper Functions
###############################################################################

pass() {
    echo -e "${GREEN}✓ PASS:${NC} $1"
    ((PASSED++))
}

fail() {
    echo -e "${RED}✗ FAIL:${NC} $1"
    ((FAILED++))
}

warn() {
    echo -e "${YELLOW}⚠ WARN:${NC} $1"
    ((WARNINGS++))
}

info() {
    echo -e "${BLUE}ℹ INFO:${NC} $1"
}

###############################################################################
# 1. Find Lambda Function
###############################################################################

echo -e "${BLUE}[1/4] Verifying Lambda Function...${NC}"
echo ""

# Find Lambda function by name pattern (Amplify creates functions with specific naming)
LAMBDA_FUNCTIONS=$(aws lambda list-functions --query "Functions[?contains(FunctionName, 'game-handler') || contains(FunctionName, 'gameHandler')].FunctionName" --output text 2>/dev/null || echo "")

if [ -z "$LAMBDA_FUNCTIONS" ]; then
    fail "No Lambda function found matching 'game-handler' or 'gameHandler'"
    LAMBDA_ARN=""
else
    # Take the first matching function
    LAMBDA_NAME=$(echo $LAMBDA_FUNCTIONS | awk '{print $1}')
    info "Found Lambda function: $LAMBDA_NAME"
    
    # Get full function details
    LAMBDA_DETAILS=$(aws lambda get-function --function-name "$LAMBDA_NAME" 2>/dev/null || echo "")
    
    if [ -z "$LAMBDA_DETAILS" ]; then
        fail "Could not retrieve Lambda function details"
        LAMBDA_ARN=""
    else
        LAMBDA_ARN=$(echo "$LAMBDA_DETAILS" | jq -r '.Configuration.FunctionArn')
        
        # Check ARM64 architecture
        ARCHITECTURE=$(echo "$LAMBDA_DETAILS" | jq -r '.Configuration.Architectures[0]')
        if [ "$ARCHITECTURE" = "arm64" ]; then
            pass "Lambda function uses ARM64 architecture (Requirement 21.1, 22.7)"
        else
            fail "Lambda function uses $ARCHITECTURE instead of ARM64 (Requirement 21.1, 22.7)"
        fi
        
        # Check runtime
        RUNTIME=$(echo "$LAMBDA_DETAILS" | jq -r '.Configuration.Runtime')
        if [[ "$RUNTIME" == python3.12* ]]; then
            pass "Lambda function uses Python 3.12 runtime"
        else
            warn "Lambda function uses $RUNTIME instead of Python 3.12"
        fi
        
        # Check memory size
        MEMORY=$(echo "$LAMBDA_DETAILS" | jq -r '.Configuration.MemorySize')
        if [ "$MEMORY" = "128" ]; then
            pass "Lambda function uses 128MB memory (cost-optimized)"
        else
            warn "Lambda function uses ${MEMORY}MB memory (expected 128MB)"
        fi
        
        # Check timeout
        TIMEOUT=$(echo "$LAMBDA_DETAILS" | jq -r '.Configuration.Timeout')
        if [ "$TIMEOUT" = "30" ]; then
            pass "Lambda function has 30 second timeout"
        else
            warn "Lambda function has ${TIMEOUT} second timeout (expected 30)"
        fi
        
        # Check Lambda tags
        if [ -n "$LAMBDA_ARN" ]; then
            LAMBDA_TAGS=$(aws lambda list-tags --resource "$LAMBDA_ARN" 2>/dev/null || echo "{}")
            
            PROJECT_TAG=$(echo "$LAMBDA_TAGS" | jq -r '.Tags.Project // .Tags.project // empty')
            MANAGED_BY_TAG=$(echo "$LAMBDA_TAGS" | jq -r '.Tags.ManagedBy // .Tags.managedBy // empty')
            ENV_TAG=$(echo "$LAMBDA_TAGS" | jq -r '.Tags.Environment // .Tags.environment // empty')
            
            if [ -n "$PROJECT_TAG" ]; then
                pass "Lambda has Project tag: $PROJECT_TAG (Requirement 24.1)"
            else
                fail "Lambda missing Project tag (Requirement 24.1)"
            fi
            
            if [ -n "$MANAGED_BY_TAG" ]; then
                pass "Lambda has ManagedBy tag: $MANAGED_BY_TAG (Requirement 24.2)"
            else
                fail "Lambda missing ManagedBy tag (Requirement 24.2)"
            fi
            
            if [ -n "$ENV_TAG" ]; then
                pass "Lambda has Environment tag: $ENV_TAG (Requirement 24.3)"
            else
                fail "Lambda missing Environment tag (Requirement 24.3)"
            fi
        fi
    fi
fi

echo ""

###############################################################################
# 2. Find and Verify DynamoDB Table
###############################################################################

echo -e "${BLUE}[2/4] Verifying DynamoDB Table...${NC}"
echo ""

# Find DynamoDB table by name pattern
DYNAMODB_TABLES=$(aws dynamodb list-tables --query "TableNames[?contains(@, 'GameSessions') || contains(@, 'game-sessions')]" --output text 2>/dev/null || echo "")

if [ -z "$DYNAMODB_TABLES" ]; then
    fail "No DynamoDB table found matching 'GameSessions' or 'game-sessions'"
    TABLE_ARN=""
else
    # Take the first matching table
    TABLE_NAME=$(echo $DYNAMODB_TABLES | awk '{print $1}')
    info "Found DynamoDB table: $TABLE_NAME"
    
    # Get table details
    TABLE_DETAILS=$(aws dynamodb describe-table --table-name "$TABLE_NAME" 2>/dev/null || echo "")
    
    if [ -z "$TABLE_DETAILS" ]; then
        fail "Could not retrieve DynamoDB table details"
        TABLE_ARN=""
    else
        TABLE_ARN=$(echo "$TABLE_DETAILS" | jq -r '.Table.TableArn')
        
        # Check billing mode
        BILLING_MODE=$(echo "$TABLE_DETAILS" | jq -r '.Table.BillingModeSummary.BillingMode // .Table.BillingMode // "PROVISIONED"')
        if [ "$BILLING_MODE" = "PAY_PER_REQUEST" ]; then
            pass "DynamoDB table uses on-demand billing (Requirement 22.3)"
        else
            fail "DynamoDB table uses $BILLING_MODE instead of PAY_PER_REQUEST (Requirement 22.3)"
        fi
        
        # Check TTL
        TTL_STATUS=$(aws dynamodb describe-time-to-live --table-name "$TABLE_NAME" 2>/dev/null | jq -r '.TimeToLiveDescription.TimeToLiveStatus')
        if [ "$TTL_STATUS" = "ENABLED" ]; then
            TTL_ATTRIBUTE=$(aws dynamodb describe-time-to-live --table-name "$TABLE_NAME" 2>/dev/null | jq -r '.TimeToLiveDescription.AttributeName')
            pass "DynamoDB table has TTL enabled on attribute: $TTL_ATTRIBUTE (Requirement 21.3)"
        else
            fail "DynamoDB table does not have TTL enabled (Requirement 21.3)"
        fi
        
        # Check partition key
        PARTITION_KEY=$(echo "$TABLE_DETAILS" | jq -r '.Table.KeySchema[] | select(.KeyType=="HASH") | .AttributeName')
        if [ "$PARTITION_KEY" = "sessionId" ]; then
            pass "DynamoDB table has correct partition key: sessionId"
        else
            warn "DynamoDB table partition key is $PARTITION_KEY (expected sessionId)"
        fi
        
        # Check DynamoDB tags
        if [ -n "$TABLE_ARN" ]; then
            DYNAMODB_TAGS=$(aws dynamodb list-tags-of-resource --resource-arn "$TABLE_ARN" 2>/dev/null || echo "{}")
            
            PROJECT_TAG=$(echo "$DYNAMODB_TAGS" | jq -r '.Tags[] | select(.Key=="Project" or .Key=="project") | .Value // empty')
            MANAGED_BY_TAG=$(echo "$DYNAMODB_TAGS" | jq -r '.Tags[] | select(.Key=="ManagedBy" or .Key=="managedBy") | .Value // empty')
            ENV_TAG=$(echo "$DYNAMODB_TAGS" | jq -r '.Tags[] | select(.Key=="Environment" or .Key=="environment") | .Value // empty')
            
            if [ -n "$PROJECT_TAG" ]; then
                pass "DynamoDB has Project tag: $PROJECT_TAG (Requirement 24.1)"
            else
                fail "DynamoDB missing Project tag (Requirement 24.1)"
            fi
            
            if [ -n "$MANAGED_BY_TAG" ]; then
                pass "DynamoDB has ManagedBy tag: $MANAGED_BY_TAG (Requirement 24.2)"
            else
                fail "DynamoDB missing ManagedBy tag (Requirement 24.2)"
            fi
            
            if [ -n "$ENV_TAG" ]; then
                pass "DynamoDB has Environment tag: $ENV_TAG (Requirement 24.3)"
            else
                fail "DynamoDB missing Environment tag (Requirement 24.3)"
            fi
        fi
    fi
fi

echo ""

###############################################################################
# 3. Verify Lambda IAM Permissions
###############################################################################

echo -e "${BLUE}[3/4] Verifying Lambda IAM Permissions...${NC}"
echo ""

if [ -n "$LAMBDA_NAME" ]; then
    # Get Lambda execution role
    LAMBDA_ROLE=$(aws lambda get-function --function-name "$LAMBDA_NAME" 2>/dev/null | jq -r '.Configuration.Role')
    
    if [ -n "$LAMBDA_ROLE" ]; then
        ROLE_NAME=$(echo "$LAMBDA_ROLE" | awk -F'/' '{print $NF}')
        info "Lambda execution role: $ROLE_NAME"
        
        # Get attached policies
        ATTACHED_POLICIES=$(aws iam list-attached-role-policies --role-name "$ROLE_NAME" 2>/dev/null | jq -r '.AttachedPolicies[].PolicyArn')
        
        # Get inline policies
        INLINE_POLICIES=$(aws iam list-role-policies --role-name "$ROLE_NAME" 2>/dev/null | jq -r '.PolicyNames[]')
        
        # Check for DynamoDB permissions
        HAS_DYNAMODB_PERMS=false
        
        # Check inline policies for DynamoDB permissions
        if [ -n "$INLINE_POLICIES" ]; then
            for POLICY_NAME in $INLINE_POLICIES; do
                POLICY_DOC=$(aws iam get-role-policy --role-name "$ROLE_NAME" --policy-name "$POLICY_NAME" 2>/dev/null | jq -r '.PolicyDocument')
                
                if echo "$POLICY_DOC" | grep -q "dynamodb"; then
                    HAS_DYNAMODB_PERMS=true
                    
                    # Check for wildcard resources
                    if echo "$POLICY_DOC" | grep -q '"Resource":\s*"\*"'; then
                        fail "Lambda IAM policy uses wildcard (*) resources (Requirement 21.2)"
                    else
                        pass "Lambda IAM policy uses specific resource ARNs (Requirement 21.2)"
                    fi
                fi
            done
        fi
        
        if [ "$HAS_DYNAMODB_PERMS" = true ]; then
            pass "Lambda has DynamoDB permissions (Requirement 21.1, 21.4)"
        else
            fail "Lambda missing DynamoDB permissions (Requirement 21.1, 21.4)"
        fi
        
        # Check for CloudWatch Logs permissions
        HAS_LOGS_PERMS=false
        if echo "$ATTACHED_POLICIES" | grep -q "AWSLambdaBasicExecutionRole"; then
            HAS_LOGS_PERMS=true
        fi
        
        if [ "$HAS_LOGS_PERMS" = true ]; then
            pass "Lambda has CloudWatch Logs permissions"
        else
            warn "Lambda may be missing CloudWatch Logs permissions"
        fi
    else
        fail "Could not retrieve Lambda execution role"
    fi
else
    fail "Cannot verify IAM permissions without Lambda function"
fi

echo ""

###############################################################################
# 4. Verify API Gateway (if deployed)
###############################################################################

echo -e "${BLUE}[4/4] Verifying API Gateway...${NC}"
echo ""

# Find API Gateway REST APIs
REST_APIS=$(aws apigateway get-rest-apis --query "items[?contains(name, 'amplify') || contains(name, 'west-of-haunted') || contains(name, 'game')].{id:id,name:name}" --output json 2>/dev/null || echo "[]")

API_COUNT=$(echo "$REST_APIS" | jq '. | length')

if [ "$API_COUNT" -eq 0 ]; then
    warn "No API Gateway REST API found (may not be deployed yet)"
    info "API Gateway is typically created when you deploy the backend to a branch"
else
    API_ID=$(echo "$REST_APIS" | jq -r '.[0].id')
    API_NAME=$(echo "$REST_APIS" | jq -r '.[0].name')
    info "Found API Gateway: $API_NAME (ID: $API_ID)"
    
    # Get API resources
    RESOURCES=$(aws apigateway get-resources --rest-api-id "$API_ID" 2>/dev/null || echo "{}")
    
    # Check for expected endpoints
    HAS_NEW_ENDPOINT=$(echo "$RESOURCES" | jq -r '.items[].path' | grep -q "/game/new" && echo "true" || echo "false")
    HAS_COMMAND_ENDPOINT=$(echo "$RESOURCES" | jq -r '.items[].path' | grep -q "/game/command" && echo "true" || echo "false")
    HAS_STATE_ENDPOINT=$(echo "$RESOURCES" | jq -r '.items[].path' | grep -q "/game/state" && echo "true" || echo "false")
    
    if [ "$HAS_NEW_ENDPOINT" = "true" ]; then
        pass "API has /game/new endpoint"
    else
        warn "API missing /game/new endpoint"
    fi
    
    if [ "$HAS_COMMAND_ENDPOINT" = "true" ]; then
        pass "API has /game/command endpoint"
    else
        warn "API missing /game/command endpoint"
    fi
    
    if [ "$HAS_STATE_ENDPOINT" = "true" ]; then
        pass "API has /game/state endpoint"
    else
        warn "API missing /game/state endpoint"
    fi
    
    # Check API Gateway tags
    API_ARN="arn:aws:apigateway:$(aws configure get region)::/restapis/$API_ID"
    API_TAGS=$(aws apigateway get-tags --resource-arn "$API_ARN" 2>/dev/null || echo "{}")
    
    PROJECT_TAG=$(echo "$API_TAGS" | jq -r '.tags.Project // .tags.project // empty')
    MANAGED_BY_TAG=$(echo "$API_TAGS" | jq -r '.tags.ManagedBy // .tags.managedBy // empty')
    ENV_TAG=$(echo "$API_TAGS" | jq -r '.tags.Environment // .tags.environment // empty')
    
    if [ -n "$PROJECT_TAG" ]; then
        pass "API Gateway has Project tag: $PROJECT_TAG (Requirement 24.1)"
    else
        fail "API Gateway missing Project tag (Requirement 24.1)"
    fi
    
    if [ -n "$MANAGED_BY_TAG" ]; then
        pass "API Gateway has ManagedBy tag: $MANAGED_BY_TAG (Requirement 24.2)"
    else
        fail "API Gateway missing ManagedBy tag (Requirement 24.2)"
    fi
    
    if [ -n "$ENV_TAG" ]; then
        pass "API Gateway has Environment tag: $ENV_TAG (Requirement 24.3)"
    else
        fail "API Gateway missing Environment tag (Requirement 24.3)"
    fi
fi

echo ""

###############################################################################
# Summary
###############################################################################

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Verification Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${GREEN}Passed:${NC}   $PASSED"
echo -e "${RED}Failed:${NC}   $FAILED"
echo -e "${YELLOW}Warnings:${NC} $WARNINGS"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All critical checks passed!${NC}"
    exit 0
else
    echo -e "${RED}✗ Some checks failed. Please review the output above.${NC}"
    exit 1
fi
