#!/bin/bash

# Deploy Amplify infrastructure with automated responses
# This script provides the required environment variable values during deployment

echo "Starting Amplify deployment..."

# Use expect to automate the interactive prompts
expect << 'EOF'
set timeout 600

spawn amplify push

# Wait for the first environment variable prompt
expect "Enter the missing environment variable value of STORAGE_GAMESESSIONS_NAME in gameHandler:"
send "#current-cloud-backend::storage::GameSessions::Name\r"

# Wait for the second environment variable prompt  
expect "Enter the missing environment variable value of STORAGE_GAMESESSIONS_ARN in gameHandler:"
send "#current-cloud-backend::storage::GameSessions::Arn\r"

# Wait for confirmation prompt
expect "Are you sure you want to continue?"
send "Y\r"

# Wait for deployment to complete
expect eof
EOF

echo "Deployment complete!"
