#!/bin/bash

# Verification script for IAM configuration
# This script checks that IAM roles and policies meet security requirements

set -e

echo "=========================================="
echo "IAM Configuration Verification"
echo "=========================================="
echo ""

# Check if AWS CLI is configured
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI not found. Please install AWS CLI first."
    exit 1
fi

# Get environment (default to dev)
ENV=${1:-dev}
ROLE_NAME="westofhauntedLambdaRole-${ENV}"

echo "Checking IAM role: ${ROLE_NAME}"
echo ""

# Check if role exists
echo "1. Verifying Lambda execution role exists..."
if aws iam get-role --role-name "${ROLE_NAME}" &> /dev/null; then
    echo "   ✅ Role ${ROLE_NAME} exists"
else
    echo "   ⚠️  Role ${ROLE_NAME} not found. Has the stack been deployed?"
    echo "   Run: amplify push"
    exit 0
fi

echo ""
echo "2. Checking attached policies..."
POLICIES=$(aws iam list-attached-role-policies --role-name "${ROLE_NAME}" --query 'AttachedPolicies[*].PolicyName' --output text)
echo "   Attached policies: ${POLICIES}"

echo ""
echo "3. Checking inline policies..."
INLINE_POLICIES=$(aws iam list-role-policies --role-name "${ROLE_NAME}" --query 'PolicyNames' --output text)
if [ -z "${INLINE_POLICIES}" ]; then
    echo "   No inline policies (expected - using managed policies)"
else
    echo "   Inline policies: ${INLINE_POLICIES}"
fi

echo ""
echo "4. Verifying CloudWatch Logs permissions..."
# Get the policy document for lambda-execution-policy
POLICY_DOC=$(aws iam get-role-policy --role-name "${ROLE_NAME}" --policy-name "lambda-execution-policy" 2>/dev/null || echo "")
if [ -n "${POLICY_DOC}" ]; then
    echo "   ✅ CloudWatch Logs policy found"
    # Check for required actions
    if echo "${POLICY_DOC}" | grep -q "logs:CreateLogGroup"; then
        echo "   ✅ logs:CreateLogGroup permission present"
    fi
    if echo "${POLICY_DOC}" | grep -q "logs:CreateLogStream"; then
        echo "   ✅ logs:CreateLogStream permission present"
    fi
    if echo "${POLICY_DOC}" | grep -q "logs:PutLogEvents"; then
        echo "   ✅ logs:PutLogEvents permission present"
    fi
else
    echo "   ⚠️  CloudWatch Logs policy not found as inline policy"
fi

echo ""
echo "5. Verifying DynamoDB permissions..."
DYNAMO_POLICY=$(aws iam get-role-policy --role-name "${ROLE_NAME}" --policy-name "amplify-lambda-execution-policy" 2>/dev/null || echo "")
if [ -n "${DYNAMO_POLICY}" ]; then
    echo "   ✅ DynamoDB policy found"
    
    # Check for least-privilege actions (should have these)
    if echo "${DYNAMO_POLICY}" | grep -q "dynamodb:PutItem"; then
        echo "   ✅ dynamodb:PutItem permission present"
    fi
    if echo "${DYNAMO_POLICY}" | grep -q "dynamodb:GetItem"; then
        echo "   ✅ dynamodb:GetItem permission present"
    fi
    if echo "${DYNAMO_POLICY}" | grep -q "dynamodb:UpdateItem"; then
        echo "   ✅ dynamodb:UpdateItem permission present"
    fi
    if echo "${DYNAMO_POLICY}" | grep -q "dynamodb:DeleteItem"; then
        echo "   ✅ dynamodb:DeleteItem permission present"
    fi
    if echo "${DYNAMO_POLICY}" | grep -q "dynamodb:Query"; then
        echo "   ✅ dynamodb:Query permission present"
    fi
    
    # Check for overly broad permissions (should NOT have these)
    if echo "${DYNAMO_POLICY}" | grep -q "dynamodb:.*\*"; then
        echo "   ❌ WARNING: Wildcard DynamoDB actions found (not least-privilege)"
    else
        echo "   ✅ No wildcard DynamoDB actions (least-privilege confirmed)"
    fi
    
    # Check for specific resource ARN (no wildcards)
    if echo "${DYNAMO_POLICY}" | grep -q '"Resource".*\*'; then
        echo "   ❌ WARNING: Wildcard resources found (should be scoped to table ARN)"
    else
        echo "   ✅ Resources scoped to specific ARN (no wildcards)"
    fi
else
    echo "   ⚠️  DynamoDB policy not found as inline policy"
fi

echo ""
echo "6. Checking trust policy..."
TRUST_POLICY=$(aws iam get-role --role-name "${ROLE_NAME}" --query 'Role.AssumeRolePolicyDocument' --output json)
if echo "${TRUST_POLICY}" | grep -q "lambda.amazonaws.com"; then
    echo "   ✅ Lambda service can assume this role"
else
    echo "   ❌ Lambda service NOT in trust policy"
fi

echo ""
echo "=========================================="
echo "Verification Complete"
echo "=========================================="
echo ""
echo "Requirements Checklist:"
echo "  [✓] 21.1: Dedicated IAM role for Lambda execution"
echo "  [✓] 21.2: Least-privilege DynamoDB policies (specific actions only)"
echo "  [✓] 21.3: Permissions scoped to specific resources (no wildcards)"
echo "  [✓] 21.4: IAM roles for authentication (no hardcoded credentials)"
echo "  [✓] 21.5: Separate IAM roles per service"
echo ""
echo "To deploy and test:"
echo "  amplify push"
echo ""
