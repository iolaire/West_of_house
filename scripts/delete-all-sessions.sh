#!/bin/bash

# Delete all corrupted game sessions from DynamoDB
# Usage: ./scripts/delete-all-sessions.sh

set -e

TABLE_NAME="GameSession-nc3wnzp2prhpvl5quuhsigh67a-NONE"
REGION="us-east-1"

echo "Fetching all session IDs from $TABLE_NAME..."

# Get all session IDs
SESSION_IDS=$(aws dynamodb scan \
  --table-name "$TABLE_NAME" \
  --region "$REGION" \
  --projection-expression "sessionId" \
  --output json | jq -r '.Items[].sessionId.S')

# Count sessions
COUNT=$(echo "$SESSION_IDS" | wc -l | tr -d ' ')
echo "Found $COUNT sessions to delete"

if [ "$COUNT" -eq 0 ]; then
  echo "No sessions found. Exiting."
  exit 0
fi

# Confirm deletion
read -p "Delete all $COUNT sessions? (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
  echo "Deletion cancelled."
  exit 0
fi

# Delete each session
DELETED=0
FAILED=0

echo "Deleting sessions..."
for SESSION_ID in $SESSION_IDS; do
  if aws dynamodb delete-item \
    --table-name "$TABLE_NAME" \
    --region "$REGION" \
    --key "{\"sessionId\": {\"S\": \"$SESSION_ID\"}}" \
    --output json > /dev/null 2>&1; then
    DELETED=$((DELETED + 1))
    echo "[$DELETED/$COUNT] Deleted: $SESSION_ID"
  else
    FAILED=$((FAILED + 1))
    echo "[$DELETED/$COUNT] FAILED: $SESSION_ID"
  fi
done

echo ""
echo "Deletion complete:"
echo "  Successfully deleted: $DELETED"
echo "  Failed: $FAILED"
echo "  Total: $COUNT"
