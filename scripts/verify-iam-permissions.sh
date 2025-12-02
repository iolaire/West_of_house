#!/bin/bash

###############################################################################
# IAM Permissions Verification Script
#
# This script verifies that the Lambda function has the correct IAM permissions
# for DynamoDB access and CloudWatch Logs, following least-privilege principles.
#
# Usage:
#   ./scripts/verify-iam-permissions.sh [function-name]
#
# Requirements: 21.1, 21.2, 21.3, 21.4
###############################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

print_header() {
    echo ""
    echo "=========================================="
    echo "$1"
    echo "=========================================="
}

# Get function name from argument or discover it
FUNCTION_NAME=$1

if [ -z "$FUNCTION_NAME" ]; then
    print_status "$YELLOW" "No function name provided. Discovering Lambda functions..."
    
    # Find Lambda functions with project tags
    FUNCTIONS=$(aws lambda list-functions \
        --query "Functions[?Tags.Project=='west-of-haunted-house'].FunctionName" \
        --output text)
    
    if [ -z "$FUNCTIONS" ]; then
        print_status "$RED" "❌ No Lambda functions found with Project=west-of-haunted-house tag"
        exit 1
    fi
    
    # Use the first function found
    FUNCTION_NAME=$(echo "$FUNCTIONS" | awk '{print $1}')
    print_status "$GREEN" "✓ Found function: $FUNCTION_NAME"
fi

print_header "Verifying IAM Permissions for $FUNCTION_NAME"

# Get the Lambda function configuration
print_status "$BLUE" "→ Fetching Lambda function configuration..."
FUNCTION_CONFIG=$(aws lambda get-function --function-name "$FUNCTION_NAME" 2>/dev/null)

if [ $? -ne 0 ]; then
    print_status "$RED" "❌ Failed to get function configuration. Function may not exist."
    exit 1
fi

# Extract the IAM role ARN
ROLE_ARN=$(echo "$FUNCTION_CONFIG" | jq -r '.Configuration.Role')
ROLE_NAME=$(echo "$ROLE_ARN" | awk -F'/' '{print $NF}')

print_status "$GREEN" "✓ Function role: $ROLE_NAME"
echo "  ARN: $ROLE_ARN"

# Get attached policies
print_header "Checking Attached IAM Policies"

print_status "$BLUE" "→ Fetching attached managed policies..."
ATTACHED_POLICIES=$(aws iam list-attached-role-policies --role-name "$ROLE_NAME" --output json)

echo "$ATTACHED_POLICIES" | jq -r '.AttachedPolicies[] | "  - \(.PolicyName) (\(.PolicyArn))"'

# Get inline policies
print_status "$BLUE" "→ Fetching inline policies..."
INLINE_POLICIES=$(aws iam list-role-policies --role-name "$ROLE_NAME" --output json)

INLINE_POLICY_NAMES=$(echo "$INLINE_POLICIES" | jq -r '.PolicyNames[]')

if [ -z "$INLINE_POLICY_NAMES" ]; then
    print_status "$YELLOW" "  No inline policies found"
else
    echo "$INLINE_POLICY_NAMES" | while read -r policy_name; do
        echo "  - $policy_name"
    done
fi

# Verify DynamoDB permissions
print_header "Verifying DynamoDB Permissions"

print_status "$BLUE" "→ Checking for DynamoDB permissions in inline policies..."

DYNAMODB_PERMISSIONS_FOUND=false

if [ -n "$INLINE_POLICY_NAMES" ]; then
    echo "$INLINE_POLICY_NAMES" | while read -r policy_name; do
        POLICY_DOC=$(aws iam get-role-policy --role-name "$ROLE_NAME" --policy-name "$policy_name" --output json)
        
        # Check if policy contains DynamoDB permissions
        if echo "$POLICY_DOC" | jq -e '.PolicyDocument.Statement[] | select(.Action[]? | contains("dynamodb"))' > /dev/null 2>&1; then
            print_status "$GREEN" "✓ Found DynamoDB permissions in policy: $policy_name"
            
            # Extract and display DynamoDB actions
            echo ""
            echo "  DynamoDB Actions:"
            echo "$POLICY_DOC" | jq -r '.PolicyDocument.Statement[] | select(.Action[]? | contains("dynamodb")) | .Action[]' | sort | uniq | sed 's/^/    - /'
            
            # Extract and display resources
            echo ""
            echo "  Resources:"
            RESOURCES=$(echo "$POLICY_DOC" | jq -r '.PolicyDocument.Statement[] | select(.Action[]? | contains("dynamodb")) | .Resource[]' 2>/dev/null || echo "")
            
            if [ -n "$RESOURCES" ]; then
                echo "$RESOURCES" | while read -r resource; do
                    if [[ "$resource" == *"*"* ]] && [[ "$resource" != *"/index/*" ]] && [[ "$resource" != *"/stream/*" ]]; then
                        print_status "$RED" "    ❌ WILDCARD DETECTED: $resource"
                        print_status "$RED" "       This violates least-privilege principle (Requirement 21.3)"
                    else
                        print_status "$GREEN" "    ✓ $resource"
                    fi
                done
            else
                print_status "$YELLOW" "    No specific resources found (may use wildcards)"
            fi
            
            DYNAMODB_PERMISSIONS_FOUND=true
        fi
    done
fi

if [ "$DYNAMODB_PERMISSIONS_FOUND" = false ]; then
    print_status "$RED" "❌ No DynamoDB permissions found in inline policies"
    print_status "$YELLOW" "   Checking managed policies..."
    
    # Check managed policies for DynamoDB permissions
    echo "$ATTACHED_POLICIES" | jq -r '.AttachedPolicies[].PolicyArn' | while read -r policy_arn; do
        POLICY_VERSION=$(aws iam get-policy --policy-arn "$policy_arn" --query 'Policy.DefaultVersionId' --output text)
        POLICY_DOC=$(aws iam get-policy-version --policy-arn "$policy_arn" --version-id "$POLICY_VERSION" --output json)
        
        if echo "$POLICY_DOC" | jq -e '.PolicyVersion.Document.Statement[] | select(.Action[]? | contains("dynamodb"))' > /dev/null 2>&1; then
            print_status "$GREEN" "✓ Found DynamoDB permissions in managed policy: $policy_arn"
        fi
    done
fi

# Verify CloudWatch Logs permissions
print_header "Verifying CloudWatch Logs Permissions"

print_status "$BLUE" "→ Checking for CloudWatch Logs permissions..."

LOGS_PERMISSIONS_FOUND=false

# Check inline policies
if [ -n "$INLINE_POLICY_NAMES" ]; then
    echo "$INLINE_POLICY_NAMES" | while read -r policy_name; do
        POLICY_DOC=$(aws iam get-role-policy --role-name "$ROLE_NAME" --policy-name "$policy_name" --output json)
        
        if echo "$POLICY_DOC" | jq -e '.PolicyDocument.Statement[] | select(.Action[]? | contains("logs:"))' > /dev/null 2>&1; then
            print_status "$GREEN" "✓ Found CloudWatch Logs permissions in policy: $policy_name"
            
            echo ""
            echo "  CloudWatch Logs Actions:"
            echo "$POLICY_DOC" | jq -r '.PolicyDocument.Statement[] | select(.Action[]? | contains("logs:")) | .Action[]' | sort | uniq | sed 's/^/    - /'
            
            echo ""
            echo "  Resources:"
            RESOURCES=$(echo "$POLICY_DOC" | jq -r '.PolicyDocument.Statement[] | select(.Action[]? | contains("logs:")) | .Resource[]' 2>/dev/null || echo "")
            
            if [ -n "$RESOURCES" ]; then
                echo "$RESOURCES" | while read -r resource; do
                    # CloudWatch Logs requires :* suffix for log streams, which is acceptable
                    if [[ "$resource" == *":log-group:/aws/lambda/"*":*" ]]; then
                        print_status "$GREEN" "    ✓ $resource (acceptable pattern for log streams)"
                    elif [[ "$resource" == *"*"* ]]; then
                        print_status "$YELLOW" "    ⚠ $resource (contains wildcard)"
                    else
                        print_status "$GREEN" "    ✓ $resource"
                    fi
                done
            fi
            
            LOGS_PERMISSIONS_FOUND=true
        fi
    done
fi

# Check managed policies for CloudWatch Logs
if [ "$LOGS_PERMISSIONS_FOUND" = false ]; then
    print_status "$YELLOW" "   Checking managed policies..."
    
    echo "$ATTACHED_POLICIES" | jq -r '.AttachedPolicies[].PolicyArn' | while read -r policy_arn; do
        if [[ "$policy_arn" == *"AWSLambdaBasicExecutionRole"* ]]; then
            print_status "$GREEN" "✓ Found AWSLambdaBasicExecutionRole (includes CloudWatch Logs permissions)"
            LOGS_PERMISSIONS_FOUND=true
        fi
    done
fi

if [ "$LOGS_PERMISSIONS_FOUND" = false ]; then
    print_status "$RED" "❌ No CloudWatch Logs permissions found"
fi

# Summary
print_header "Verification Summary"

echo ""
print_status "$BLUE" "Requirements Checklist:"
echo ""
echo "  21.1 - Dedicated IAM role for Lambda execution:"
print_status "$GREEN" "    ✓ Role: $ROLE_NAME"
echo ""
echo "  21.2 - Least-privilege DynamoDB permissions:"
if [ "$DYNAMODB_PERMISSIONS_FOUND" = true ]; then
    print_status "$GREEN" "    ✓ DynamoDB permissions configured"
else
    print_status "$RED" "    ❌ DynamoDB permissions not found"
fi
echo ""
echo "  21.3 - Permissions scoped to specific resources (no wildcards):"
print_status "$YELLOW" "    ⚠ Review resources above for wildcard usage"
echo ""
echo "  21.4 - CloudWatch Logs permissions for debugging:"
if [ "$LOGS_PERMISSIONS_FOUND" = true ]; then
    print_status "$GREEN" "    ✓ CloudWatch Logs permissions configured"
else
    print_status "$RED" "    ❌ CloudWatch Logs permissions not found"
fi
echo ""

print_status "$GREEN" "✓ Verification complete!"
echo ""
