import { defineBackend } from '@aws-amplify/backend';
import { auth } from './auth/resource';
import { data } from './data/resource';
import { gameHandler } from './functions/game-handler/resource';

/**
 * West of Haunted House Backend Definition
 * 
 * This defines the AWS Amplify Gen 2 backend infrastructure:
 * - Authentication (Cognito Identity Pool for guest access)
 * - Data (DynamoDB GameSessions table via Amplify Data)
 * - Lambda Function (Game handler for command processing)
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
  gameHandler,
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

/**
 * Grant Lambda function access to DynamoDB table
 * 
 * This grants the game handler Lambda function read/write permissions
 * to the GameSessions DynamoDB table using least-privilege IAM policies.
 * 
 * Requirements: 21.1, 21.2, 21.3, 21.4
 */
const { Table } = await import('aws-cdk-lib/aws-dynamodb');
const gameSessionsTable = Table.fromTableName(
  stack,
  'GameSessionsTable',
  'WestOfHauntedHouse-GameSessions'
);

// Grant read/write access to the Lambda function
gameSessionsTable.grantReadWriteData(backend.gameHandler.resources.lambda);

// Set the table name as an environment variable
backend.gameHandler.addEnvironment('GAME_SESSIONS_TABLE_NAME', gameSessionsTable.tableName);
