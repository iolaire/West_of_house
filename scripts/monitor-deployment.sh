#!/bin/bash

# Monitor AWS Amplify deployment status
# Usage: ./scripts/monitor-deployment.sh

APP_ID="dhi9gcvt4p94z"
BRANCH_NAME="production"
LIVE_URL="https://production.dhi9gcvt4p94z.amplifyapp.com"

echo "=========================================="
echo "AWS Amplify Deployment Monitor"
echo "=========================================="
echo "App ID: $APP_ID"
echo "Branch: $BRANCH_NAME"
echo "Live URL: $LIVE_URL"
echo "=========================================="
echo ""

# Get latest job status
echo "📊 Checking deployment status..."
JOB_STATUS=$(aws amplify list-jobs \
  --app-id $APP_ID \
  --branch-name $BRANCH_NAME \
  --max-results 1 \
  --query 'jobSummaries[0].status' \
  --output text)

JOB_ID=$(aws amplify list-jobs \
  --app-id $APP_ID \
  --branch-name $BRANCH_NAME \
  --max-results 1 \
  --query 'jobSummaries[0].jobId' \
  --output text)

echo "Current Status: $JOB_STATUS"
echo "Job ID: $JOB_ID"
echo ""

# Get detailed job information
if [ "$JOB_STATUS" = "RUNNING" ]; then
  echo "🔄 Deployment in progress..."
  echo ""
  echo "Build Steps:"
  aws amplify get-job \
    --app-id $APP_ID \
    --branch-name $BRANCH_NAME \
    --job-id $JOB_ID \
    --query 'job.steps[*].[stepName,status]' \
    --output table
  echo ""
  echo "⏳ Waiting for deployment to complete..."
  echo "   Check AWS Console: https://console.aws.amazon.com/amplify/home?region=us-east-1#/$APP_ID/$BRANCH_NAME/$JOB_ID"
  
elif [ "$JOB_STATUS" = "SUCCEED" ]; then
  echo "✅ Deployment successful!"
  echo ""
  echo "🌐 Live Application URL:"
  echo "   $LIVE_URL"
  echo ""
  echo "📋 Next Steps:"
  echo "   1. Open the URL in your browser"
  echo "   2. Test core functionality (commands, images, transitions)"
  echo "   3. Check CloudWatch logs for any errors"
  echo "   4. Monitor CloudWatch metrics"
  echo ""
  
elif [ "$JOB_STATUS" = "FAILED" ]; then
  echo "❌ Deployment failed!"
  echo ""
  echo "📋 Check build logs:"
  echo "   https://console.aws.amazon.com/amplify/home?region=us-east-1#/$APP_ID/$BRANCH_NAME/$JOB_ID"
  echo ""
  echo "🔍 Common issues:"
  echo "   - Node version mismatch (check .nvmrc)"
  echo "   - Missing dependencies (check package.json)"
  echo "   - TypeScript errors (run: npx tsc --noEmit)"
  echo "   - Environment variables (check .env.production)"
  echo ""
  
else
  echo "⚠️  Unknown status: $JOB_STATUS"
fi

echo ""
echo "=========================================="
echo "CloudWatch Metrics"
echo "=========================================="

# Check Lambda function
LAMBDA_FUNCTION=$(aws lambda list-functions \
  --query "Functions[?contains(FunctionName, 'gamehandler')].FunctionName | [0]" \
  --output text 2>/dev/null)

if [ "$LAMBDA_FUNCTION" != "None" ] && [ -n "$LAMBDA_FUNCTION" ]; then
  echo "Lambda Function: $LAMBDA_FUNCTION"
  
  # Get recent invocations
  INVOCATIONS=$(aws cloudwatch get-metric-statistics \
    --namespace AWS/Lambda \
    --metric-name Invocations \
    --dimensions Name=FunctionName,Value=$LAMBDA_FUNCTION \
    --start-time $(date -u -v-1H +%Y-%m-%dT%H:%M:%S) \
    --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
    --period 3600 \
    --statistics Sum \
    --query 'Datapoints[0].Sum' \
    --output text 2>/dev/null)
  
  if [ "$INVOCATIONS" != "None" ] && [ -n "$INVOCATIONS" ]; then
    echo "  Invocations (last hour): $INVOCATIONS"
  else
    echo "  Invocations (last hour): 0"
  fi
  
  # Get recent errors
  ERRORS=$(aws cloudwatch get-metric-statistics \
    --namespace AWS/Lambda \
    --metric-name Errors \
    --dimensions Name=FunctionName,Value=$LAMBDA_FUNCTION \
    --start-time $(date -u -v-1H +%Y-%m-%dT%H:%M:%S) \
    --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
    --period 3600 \
    --statistics Sum \
    --query 'Datapoints[0].Sum' \
    --output text 2>/dev/null)
  
  if [ "$ERRORS" != "None" ] && [ -n "$ERRORS" ]; then
    echo "  Errors (last hour): $ERRORS"
  else
    echo "  Errors (last hour): 0"
  fi
else
  echo "Lambda function not found or not yet deployed"
fi

echo ""
echo "=========================================="
echo "Quick Commands"
echo "=========================================="
echo "Test API endpoint:"
echo "  curl -X POST https://\$API_ENDPOINT/game -H 'Content-Type: application/json' -d '{\"command\": \"look\"}'"
echo ""
echo "View Lambda logs:"
echo "  aws logs tail /aws/lambda/\$FUNCTION_NAME --follow"
echo ""
echo "Check DynamoDB table:"
echo "  aws dynamodb describe-table --table-name \$TABLE_NAME"
echo ""
echo "Monitor costs:"
echo "  aws ce get-cost-and-usage --time-period Start=\$(date -v-7d +%Y-%m-%d),End=\$(date +%Y-%m-%d) --granularity DAILY --metrics BlendedCost"
echo ""
