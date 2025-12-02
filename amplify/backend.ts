import { defineBackend } from '@aws-amplify/backend';
import { auth } from './auth/resource';
import { data } from './data/resource';

/**
 * West of Haunted House Backend Definition
 * 
 * This defines the AWS Amplify Gen 2 backend infrastructure for task 17.3.2:
 * - Authentication (Cognito Identity Pool for guest access)
 * - Data (DynamoDB GameSessions table via Amplify Data)
 * 
 * Note: Lambda function and API Gateway will be added in subsequent tasks (17.3.3+)
 * 
 * All resources are automatically tagged with:
 * - Project: west-of-haunted-house
 * - ManagedBy: vedfolnir
 * - Environment: dev/staging/prod (from AMPLIFY_ENV)
 * 
 * Requirements: 22.3, 22.4, 24.1, 24.2, 24.3
 * 
 * @see https://docs.amplify.aws/react/build-a-backend/
 */
const backend = defineBackend({
  auth,
  data,
});

/**
 * Apply required resource tags to all AWS resources
 * 
 * These tags enable:
 * - Cost tracking and allocation
 * - Resource discovery and management
 * - Automated cleanup scripts
 * - Compliance and governance
 * 
 * Requirements: 24.1, 24.2, 24.3, 24.4
 */
const { Stack } = await import('aws-cdk-lib');
const { Tags } = await import('aws-cdk-lib');

// Get the stack to apply tags
const stack = Stack.of(backend.data);

// Apply required tags to all resources in the stack
Tags.of(stack).add('Project', 'west-of-haunted-house');
Tags.of(stack).add('ManagedBy', 'vedfolnir');
Tags.of(stack).add('Environment', process.env.AMPLIFY_ENV || 'dev');
