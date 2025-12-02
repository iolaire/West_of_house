# Domain Safety Guarantee

## Your Custom Domain is Protected

**Domain:** west.zero.vedfolnir.org

This document guarantees that your custom domain configuration is **100% safe** during all deployment and cleanup operations.

## What is Protected

### ✅ Always Preserved (Never Deleted)

1. **Amplify App**
   - The Amplify app container that hosts your application
   - App ID and configuration
   - Build settings and environment

2. **Custom Domain Configuration**
   - Domain name: west.zero.vedfolnir.org
   - Domain association with Amplify app
   - SSL/TLS certificate
   - Certificate validation records

3. **Route 53 DNS**
   - DNS records pointing to Amplify
   - Hosted zone configuration
   - All DNS routing rules

4. **GitHub Integration**
   - Repository connection
   - Branch configuration
   - Webhook settings
   - Automatic deployment triggers

5. **Amplify Service Roles**
   - IAM roles for Amplify service
   - Permissions for hosting and deployment

## What Gets Cleaned Up

### ❌ Backend Resources Only (Safely Removed)

1. **Lambda Functions**
   - game-handler function
   - Function code and configuration
   - CloudWatch log groups

2. **DynamoDB Tables**
   - GameSessions table
   - Session data (temporary by design)

3. **API Gateway**
   - REST API endpoints
   - API stages and deployments

4. **Lambda Execution Roles**
   - IAM roles for Lambda functions only
   - Does NOT touch Amplify service roles

## How Protection Works

### Cleanup Script Safety

The `cleanup-backend.sh` script:

1. **Never calls Amplify delete commands**
   - No `aws amplify delete-app`
   - No `aws amplify delete-domain-association`
   - No Route 53 record deletion

2. **Tag-based filtering**
   - Only deletes resources with specific tags
   - Amplify app has different tags
   - Domain resources are not tagged for deletion

3. **Explicit role exclusion**
   - Skips any role containing "amplify" (except Lambda roles)
   - Preserves Amplify service roles

4. **Verification before cleanup**
   - Checks Amplify app exists
   - Displays custom domain configuration
   - Confirms domain will be preserved

### Deployment Script Safety

The `deploy-gen2.sh` script:

1. **Never recreates Amplify app**
   - Uses existing app infrastructure
   - Only updates backend resources

2. **Preserves domain configuration**
   - Doesn't modify domain associations
   - Doesn't touch SSL certificates
   - Doesn't change DNS records

3. **Displays domain status**
   - Shows custom domain after deployment
   - Confirms domain is intact

## Verification Commands

### Check Amplify App Status

```bash
aws amplify list-apps --region us-east-1 \
  --query "apps[?tags.Project=='west-of-haunted-house']"
```

### Check Custom Domain

```bash
# Get app ID first
APP_ID=$(aws amplify list-apps --region us-east-1 \
  --query "apps[?tags.Project=='west-of-haunted-house'].appId" \
  --output text)

# Check domain associations
aws amplify list-domain-associations --app-id $APP_ID --region us-east-1
```

### Check Route 53 Records

```bash
# List hosted zones
aws route53 list-hosted-zones-by-name --dns-name vedfolnir.org

# Get zone ID and check records
ZONE_ID="your-zone-id"
aws route53 list-resource-record-sets --hosted-zone-id $ZONE_ID \
  --query "ResourceRecordSets[?Name=='west.zero.vedfolnir.org.']"
```

## Deployment Workflow

### Safe Cleanup and Redeploy

```bash
# 1. Verify domain before cleanup
aws amplify list-domain-associations --app-id $APP_ID --region us-east-1

# 2. Clean up backend (domain preserved)
./scripts/cleanup-backend.sh

# 3. Verify domain still exists
aws amplify list-domain-associations --app-id $APP_ID --region us-east-1

# 4. Redeploy backend
./scripts/deploy-gen2.sh --type sandbox

# 5. Verify domain still works
curl https://west.zero.vedfolnir.org
```

### Expected Output

After cleanup, you should see:
```
✓ Backend resources removed
✓ Amplify app preserved
✓ Custom domain preserved: west.zero.vedfolnir.org
✓ Route 53 configuration intact
✓ GitHub connection maintained
```

## Why This Matters

Setting up custom domains with Route 53 is time-consuming:

1. **Domain Association** - Connecting domain to Amplify app
2. **SSL Certificate** - Requesting and validating certificate
3. **DNS Propagation** - Waiting for DNS changes to propagate (can take hours)
4. **Certificate Validation** - Waiting for SSL validation (can take 30+ minutes)

By preserving the domain configuration, you can:
- Clean up and redeploy as many times as needed
- Test different backend configurations
- Iterate quickly without waiting for DNS/SSL
- Never lose your domain setup

## Emergency Recovery

If domain configuration is accidentally deleted:

1. **Reconnect Domain in Amplify Console**
   - Go to Amplify Console → App Settings → Domain management
   - Add custom domain: west.zero.vedfolnir.org
   - Follow SSL certificate validation steps

2. **Update Route 53 Records**
   - Amplify will provide new DNS records
   - Update CNAME records in Route 53
   - Wait for DNS propagation (up to 48 hours)

3. **Verify SSL Certificate**
   - Check certificate status in Amplify Console
   - May need to re-validate via DNS or email

## Support

If you have concerns about domain safety:

1. **Always use dry-run first**
   ```bash
   ./scripts/cleanup-backend.sh --dry-run
   ```

2. **Check what will be deleted**
   - Review the list of resources
   - Verify no Amplify app or domain resources listed

3. **Verify after operations**
   - Check Amplify Console
   - Test domain access
   - Review Route 53 records

## Guarantee

**We guarantee that:**
- The cleanup script will NEVER delete your Amplify app
- The cleanup script will NEVER delete domain associations
- The cleanup script will NEVER modify Route 53 records
- The deployment script will NEVER recreate the Amplify app
- Your domain west.zero.vedfolnir.org is 100% safe

You can clean up and redeploy as many times as needed without any risk to your domain configuration.
