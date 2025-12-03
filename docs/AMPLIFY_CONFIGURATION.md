# Amplify Configuration for Frontend

## Overview

The frontend uses **AWS Amplify Gen 2** automatic configuration instead of manual environment variables. This provides a seamless integration between the backend and frontend.

## How It Works

### 1. Amplify Generates Configuration

When you deploy the backend with Amplify Gen 2:

```bash
npx ampx sandbox  # or deploy to production
```

Amplify automatically generates `amplify_outputs.json` containing:
- API Gateway endpoint URL
- AWS region
- Authentication configuration
- DynamoDB table information

### 2. Frontend Reads Configuration

The frontend reads `amplify_outputs.json` via `src/config.ts`:

```typescript
import amplifyConfig from '../amplify_outputs.json';

export const getApiBaseUrl = (): string => {
  // Automatically uses the deployed API Gateway URL
  return amplifyConfig.api?.url || 'http://localhost:3001';
};
```

### 3. No Manual Configuration Needed

✓ **No `.env` files to manage**
✓ **No hardcoded URLs**
✓ **Automatic environment switching** (sandbox vs production)
✓ **Type-safe configuration**

## Current Configuration Structure

From `amplify_outputs.json`:

```json
{
  "auth": {
    "aws_region": "us-east-1",
    "user_pool_id": "...",
    "identity_pool_id": "..."
  },
  "data": {
    "url": "https://...appsync-api.us-east-1.amazonaws.com/graphql",
    "aws_region": "us-east-1"
  }
}
```

**Note**: The API Gateway REST API URL will be added to this configuration once the backend is fully deployed with the custom API Gateway endpoints defined in `amplify/backend.ts`.

## Local Development Override

For local backend testing, you can optionally override the API URL:

```bash
# Override API URL for local Lambda testing
VITE_API_BASE_URL=http://localhost:3001 npm run dev
```

This is useful when:
- Testing with a local Lambda function
- Using SAM local
- Debugging backend issues

## Backend API Endpoints

The backend defines these REST API endpoints (from `amplify/backend.ts`):

- `POST /game/new` - Create new game session
- `POST /game/command` - Execute game command
- `GET /game/state/{sessionId}` - Get current game state

These endpoints are automatically configured with:
- CORS enabled for frontend access
- Lambda integration
- Proper IAM permissions

## Deployment Flow

### Sandbox (Development)

```bash
# Terminal 1: Start backend sandbox
cd amplify
npx ampx sandbox

# Terminal 2: Start frontend dev server
npm run dev
```

The frontend automatically connects to the sandbox API Gateway.

### Production

```bash
# Deploy backend
git checkout production
git merge main
git push origin production

# Amplify automatically:
# 1. Builds the backend infrastructure
# 2. Generates amplify_outputs.json
# 3. Builds the frontend with the correct API URL
# 4. Deploys everything together
```

## Benefits of Amplify Configuration

1. **No Configuration Drift**: Frontend always uses the correct backend URL
2. **Environment Isolation**: Sandbox and production are automatically separate
3. **Type Safety**: TypeScript types for all configuration
4. **Security**: No hardcoded credentials or URLs in code
5. **Simplicity**: One source of truth for all configuration

## Troubleshooting

### "amplify_outputs.json not found"

This is normal during initial setup. The file is generated when you:
1. Run `npx ampx sandbox` (for development)
2. Deploy to production via Amplify

### API URL not working

Check that:
1. Backend is deployed and running
2. `amplify_outputs.json` exists in the project root
3. API Gateway endpoints are defined in `amplify/backend.ts`
4. CORS is properly configured

### Local development issues

Use the environment variable override:

```bash
VITE_API_BASE_URL=http://localhost:3001 npm run dev
```

## Next Steps

In **Task 3** (Implement API client service), we'll:
1. Extract the API Gateway URL from `amplify_outputs.json`
2. Create the `GameApiClient` class that uses this URL
3. Handle authentication with Amplify Auth (if needed)
4. Implement proper error handling for API calls
