#!/bin/bash
# Clear all game sessions from DynamoDB tables
# Use this after deploying changes that affect game state structure

set -e

REGION="us-east-1"

echo "🗑️  Clearing game sessions from DynamoDB..."

# Get all GameSession tables
TABLES=$(aws dynamodb list-tables --region $REGION --output json | jq -r '.TableNames[] | select(startswith("GameSession-"))')

for TABLE in $TABLES; do
    echo ""
    echo "📋 Processing table: $TABLE"
    
    # Get count
    COUNT=$(aws dynamodb scan --table-name "$TABLE" --region $REGION --select COUNT --output json | jq -r '.Count')
    echo "   Found $COUNT sessions"
    
    if [ "$COUNT" -eq 0 ]; then
        echo "   ✓ Table is already empty"
        continue
    fi
    
    # Get all items (just the keys)
    echo "   Scanning for session IDs..."
    ITEMS=$(aws dynamodb scan \
        --table-name "$TABLE" \
        --region $REGION \
        --projection-expression "sessionId" \
        --output json | jq -r '.Items[].sessionId.S')
    
    # Delete each item
    DELETED=0
    for SESSION_ID in $ITEMS; do
        aws dynamodb delete-item \
            --table-name "$TABLE" \
            --region $REGION \
            --key "{\"id\": {\"S\": \"$SESSION_ID\"}}" \
            --output json > /dev/null
        DELETED=$((DELETED + 1))
        
        # Progress indicator
        if [ $((DELETED % 10)) -eq 0 ]; then
            echo "   Deleted $DELETED/$COUNT sessions..."
        fi
    done
    
    echo "   ✓ Deleted $DELETED sessions from $TABLE"
done

echo ""
echo "✅ All game sessions cleared!"
echo ""
echo "💡 Tip: Clear localStorage in your browser to start fresh:"
echo "   localStorage.clear()"
