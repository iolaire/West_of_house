/**
 * Application configuration
 * 
 * This file reads configuration from Amplify outputs (amplify_outputs.json)
 * which is automatically generated during deployment.
 * 
 * Note: The frontend now uses AppSync GraphQL API for all game operations.
 * The REST API configuration below is kept for backward compatibility with
 * the legacy GameApiClient, but GraphQLApiClient is the primary client.
 * 
 * For local development, you can override the API URL by setting:
 * VITE_API_BASE_URL environment variable
 */

// Import Amplify outputs (generated during deployment)
// This file contains all backend configuration including API endpoints
let amplifyConfig: any = {};

try {
  // Try to import amplify_outputs.json if it exists
  amplifyConfig = await import('../amplify_outputs.json');
} catch (error) {
  console.warn('amplify_outputs.json not found. Using environment variables or defaults.');
}

/**
 * Get the API base URL
 * Priority:
 * 1. Environment variable (for local development override)
 * 2. Amplify outputs (from deployment)
 * 3. Default localhost (fallback)
 */
export const getApiBaseUrl = (): string => {
  // Check for environment variable override
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL;
  }
  
  // TODO: Extract API Gateway URL from amplify_outputs.json
  // Once the API Gateway is deployed, the URL will be available in amplify_outputs.json
  // For now, we'll use a placeholder that will be updated in Task 3
  
  // Fallback to localhost for local development
  return 'http://localhost:3001';
};

/**
 * Get the API timeout in milliseconds
 */
export const getApiTimeout = (): number => {
  const timeout = import.meta.env.VITE_API_TIMEOUT;
  return timeout ? parseInt(timeout, 10) : 30000; // Default 30 seconds
};

/**
 * Check if analytics is enabled
 */
export const isAnalyticsEnabled = (): boolean => {
  return import.meta.env.VITE_ENABLE_ANALYTICS === 'true';
};

/**
 * Get AWS region from Amplify config
 */
export const getAwsRegion = (): string => {
  return amplifyConfig.auth?.aws_region || 'us-east-1';
};

/**
 * Export the full Amplify configuration for use with Amplify libraries
 */
export const amplifyConfiguration = amplifyConfig;
