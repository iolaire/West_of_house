#!/bin/bash

# Setup script for creating the AWS deployment IAM user
# This script creates the West_of_house_AmplifyDeploymentUser with necessary permissions

set -e

USER_NAME="West_of_house_AmplifyDeploymentUser"
POLICY_NAME="AmplifyDeploymentPolicy"
POLICY_FILE="scripts/iam-deployment-policy.json"

echo "=========================================="
echo "AWS Deployment User Setup"
echo "=========================================="
echo ""

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "ERROR: AWS CLI is not installed. Please install it first."
    echo "Visit: https://aws.amazon.com/cli/"
    exit 1
fi

# Check if policy file exists
if [ ! -f "$POLICY_FILE" ]; then
    echo "ERROR: Policy file not found at $POLICY_FILE"
    exit 1
fi

echo "Step 1: Creating IAM user '$USER_NAME'..."
if aws iam create-user --user-name "$USER_NAME" 2>/dev/null; then
    echo "✓ User created successfully"
else
    echo "⚠ User may already exist, continuing..."
fi

echo ""
echo "Step 2: Attaching deployment policy..."
aws iam put-user-policy \
    --user-name "$USER_NAME" \
    --policy-name "$POLICY_NAME" \
    --policy-document file://"$POLICY_FILE"
echo "✓ Policy attached successfully"

echo ""
echo "Step 3: Creating access keys..."
ACCESS_KEY_OUTPUT=$(aws iam create-access-key --user-name "$USER_NAME")

ACCESS_KEY_ID=$(echo "$ACCESS_KEY_OUTPUT" | grep -o '"AccessKeyId": "[^"]*' | cut -d'"' -f4)
SECRET_ACCESS_KEY=$(echo "$ACCESS_KEY_OUTPUT" | grep -o '"SecretAccessKey": "[^"]*' | cut -d'"' -f4)

echo "✓ Access keys created"
echo ""
echo "=========================================="
echo "IMPORTANT: Save these credentials securely!"
echo "=========================================="
echo ""
echo "Access Key ID: $ACCESS_KEY_ID"
echo "Secret Access Key: $SECRET_ACCESS_KEY"
echo ""
echo "⚠ WARNING: These credentials will not be shown again!"
echo "⚠ Store them in a secure location (password manager, AWS Secrets Manager, etc.)"
echo ""

echo "Step 4: Configuring AWS CLI profile 'amplify-deploy'..."
echo ""
echo "Run the following command to configure your AWS CLI:"
echo ""
echo "  aws configure --profile amplify-deploy"
echo ""
echo "When prompted, enter:"
echo "  AWS Access Key ID: $ACCESS_KEY_ID"
echo "  AWS Secret Access Key: $SECRET_ACCESS_KEY"
echo "  Default region name: us-east-1 (or your preferred region)"
echo "  Default output format: json"
echo ""
echo "=========================================="
echo "Next Steps:"
echo "=========================================="
echo ""
echo "1. Configure the AWS CLI profile as shown above"
echo "2. Test the profile: aws sts get-caller-identity --profile amplify-deploy"
echo "3. Use the profile for deployments: export AWS_PROFILE=amplify-deploy"
echo "4. Add AWS_PROFILE=amplify-deploy to your .env file (DO NOT commit to git)"
echo ""
echo "Setup complete!"
