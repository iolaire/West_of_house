# Deployment Guide

This document describes how to deploy the Grimoire Frontend to AWS Amplify.

## Prerequisites

- AWS Account with Amplify access
- Git repository connected to AWS Amplify
- Node.js 20+ and npm 10+ installed locally

## Deployment Architecture

The application uses AWS Amplify Gen 2 with a two-branch deployment strategy:

- **`main` branch**: Development and testing (does NOT trigger deployments)
- **`production` branch**: Production deployments (triggers automatic AWS deployment)

## Environment Configuration

### Environment Variables

The application uses Vite's environment variable system with three configuration files:

1. **`.env.development`** - Local development settings
   - Used when running `npm run dev`
   - Lower timeout for faster feedback
   - Analytics disabled

2. **`.env.production`** - Production build settings
   - Used when running `npm run build` or deploying to Amplify
   - Higher timeout for reliability
   - Analytics enabled

3. **`.env.local`** - Local overrides (gitignored)
   - Optional file for developer-specific settings
   - Overrides both development and production settings
   - Never committed to version control

### Available Environment Variables

- `VITE_API_TIMEOUT` - API request timeout in milliseconds (default: 30000 for production, 10000 for development)
- `VITE_ENABLE_ANALYTICS` - Enable/disable analytics (default: true for production, false for development)

**Note**: The API base URL is automatically configured from `amplify_outputs.json` and does not need to be set manually.

## Build Configuration

### amplify.yml

The `amplify.yml` file configures the Amplify build process:

```yaml
version: 1
backend:
  phases:
    preBuild:
      - Install Node.js 20
      - Install dependencies
    build:
      - Deploy backend infrastructure (Lambda, DynamoDB, API Gateway)

frontend:
  phases:
    preBuild:
      - Install frontend dependencies
    build:
      - Copy images to public directory
      - Convert images to WebP format
      - Build React application with Vite
  artifacts:
    - Output directory: dist/
  cache:
    - Cache node_modules for faster builds
  customHeaders:
    - Long cache headers for static assets (1 year)
    - Security headers for all responses
```

### Cache Headers

Static assets are cached aggressively to reduce costs and improve performance:

- **Images** (PNG, WebP): 1 year cache (`max-age=31536000, immutable`)
- **JavaScript/CSS**: 1 year cache (content-hashed filenames ensure cache busting)
- **HTML**: No cache (`max-age=0, must-revalidate`) to ensure users get latest version

### Security Headers

All responses include security headers:

- `X-Content-Type-Options: nosniff` - Prevent MIME type sniffing
- `X-Frame-Options: DENY` - Prevent clickjacking
- `X-XSS-Protection: 1; mode=block` - Enable XSS protection
- `Referrer-Policy: strict-origin-when-cross-origin` - Control referrer information

## Deployment Process

### Automatic Deployment (Recommended)

1. **Develop on `main` branch**:
   ```bash
   git checkout main
   git pull origin main
   # Make changes
   git add .
   git commit -m "Feature: description"
   git push origin main
   ```

2. **Deploy to production**:
   ```bash
   git checkout production
   git merge main --no-edit
   git push origin production
   ```

3. **Monitor deployment**:
   - Go to AWS Amplify Console
   - Watch build progress (typically 5-12 minutes)
   - Verify deployment success

4. **Sync branches**:
   ```bash
   git checkout main
   git merge production
   git push origin main
   ```

### Manual Deployment (Alternative)

If you need to deploy manually:

```bash
# Build locally
npm run build

# Deploy using Amplify CLI
npx ampx pipeline-deploy --branch production --app-id <your-app-id>
```

## Testing Deployment

### Sandbox Environment

Test changes in a sandbox environment before deploying to production:

```bash
# Start sandbox (creates per-developer cloud environment)
npx ampx sandbox

# In another terminal, run the frontend
npm run dev
```

The sandbox creates isolated AWS resources for testing without affecting production.

### Production Verification

After deploying to production:

1. **Check build logs** in Amplify Console
2. **Verify resources** are created:
   - Lambda functions
   - DynamoDB tables
   - API Gateway endpoints
3. **Test the application**:
   - Visit the Amplify-provided URL
   - Create a new game session
   - Send commands and verify responses
   - Check image loading and transitions
4. **Monitor CloudWatch Logs** for errors

## Cost Optimization

The deployment is optimized for cost efficiency:

### Build Costs
- ~4 minutes per build
- ~10 builds per month
- **Cost**: ~$0.40/month

### Data Transfer
- Lazy loading reduces initial transfer
- Browser caching reduces repeat visits
- WebP compression reduces image sizes
- **Cost**: ~$0.73/month (optimized) or ~$2.80/month (unoptimized)

### Total Estimated Cost
- **Optimized**: ~$1.23/month (backend + frontend)
- **Unoptimized**: ~$3.30/month
- **With AWS Free Tier**: $0.00/month for first 12 months

### Cost Monitoring

Set up AWS Budgets to alert when costs exceed thresholds:

```bash
# Create budget alert for $5/month
aws budgets create-budget \
  --account-id <your-account-id> \
  --budget file://budget-config.json
```

## Troubleshooting

### Build Failures

**Problem**: Build fails with "npm ci" error
**Solution**: Delete `package-lock.json` and run `npm install` locally, then commit

**Problem**: Image conversion fails
**Solution**: Ensure `scripts/convert-images-to-webp.sh` has execute permissions

**Problem**: TypeScript errors during build
**Solution**: Run `npx tsc --noEmit` locally to check for type errors

### Deployment Failures

**Problem**: Backend deployment fails
**Solution**: Check Amplify Console logs for specific error, verify IAM permissions

**Problem**: Frontend builds but doesn't load
**Solution**: Check browser console for errors, verify API endpoint in `amplify_outputs.json`

**Problem**: Images not loading
**Solution**: Verify images are in `public/images/` directory, check cache headers

### Runtime Issues

**Problem**: API calls fail with CORS errors
**Solution**: Verify API Gateway CORS configuration in `amplify/backend.ts`

**Problem**: Session not persisting
**Solution**: Check localStorage in browser DevTools, verify session ID is stored

**Problem**: Images load slowly
**Solution**: Verify cache headers are set, check WebP conversion, enable lazy loading

## Rollback

If a deployment causes issues:

```bash
# Revert production branch to previous commit
git checkout production
git revert HEAD
git push origin production

# Or reset to specific commit
git reset --hard <previous-commit-hash>
git push origin production --force
```

## Monitoring

### CloudWatch Metrics

Monitor these metrics in AWS CloudWatch:

- **Lambda Invocations**: Number of API calls
- **Lambda Duration**: Response time
- **Lambda Errors**: Failed requests
- **DynamoDB Read/Write Units**: Database usage
- **API Gateway 4xx/5xx**: Client/server errors

### Amplify Metrics

Monitor in Amplify Console:

- **Build Duration**: Time to build and deploy
- **Build Success Rate**: Percentage of successful builds
- **Data Transfer**: Bandwidth usage
- **Request Count**: Number of page loads

## Security

### Best Practices

- ✅ All API calls use HTTPS
- ✅ Security headers enabled
- ✅ No sensitive data in environment variables
- ✅ IAM roles with least-privilege permissions
- ✅ Session IDs are UUIDs (not predictable)
- ✅ Input sanitization on backend

### Regular Maintenance

- Rotate AWS access keys every 90 days
- Update dependencies monthly (`npm update`)
- Review CloudWatch logs for suspicious activity
- Monitor AWS Budgets for unexpected costs

## Additional Resources

- [AWS Amplify Documentation](https://docs.amplify.aws/)
- [Vite Documentation](https://vitejs.dev/)
- [React Documentation](https://react.dev/)
- [Git Workflow Guide](git-workflow.md)
- [Technology Stack](tech.md)
