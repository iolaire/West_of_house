import { defineBackend } from '@aws-amplify/backend';
import { RemovalPolicy } from 'aws-cdk-lib';
import { AttributeType, BillingMode, Table } from 'aws-cdk-lib/aws-dynamodb';
import { gameHandler } from './functions/game-handler/resource';

/**
 * West of Haunted House Backend Definition
 * 
 * This defines the AWS Amplify Gen 2 backend infrastructure including:
 * - DynamoDB GameSessions table (created with CDK)
 * - Lambda game handler for command processing
 * 
 * Authentication is deferred to a future phase. For MVP, the API will be publicly accessible.
 * 
 * All resources are automatically tagged with:
 * - Project: west-of-haunted-house
 * - ManagedBy: vedfolnir
 * - Environment: dev/staging/prod (from AMPLIFY_ENV)
 * 
 * Requirements: 22.4, 22.6, 24.1, 24.2, 24.3
 * 
 * @see https://docs.amplify.aws/react/build-a-backend/
 */
const backend = defineBackend({
  gameHandler,
});

/**
 * Create DynamoDB table for game sessions using CDK
 * 
 * We use CDK directly instead of defineData because:
 * - We need a REST API, not GraphQL
 * - defineData creates AppSync GraphQL resolvers which we don't need
 * - Direct CDK gives us full control over table configuration
 * 
 * Note: We add the table to the gameHandler stack to avoid nested stack issues in sandbox
 */
const gameHandlerStack = backend.gameHandler.resources.lambda.stack;

const gameSessionsTable = new Table(gameHandlerStack, 'GameSessions', {
  partitionKey: {
    name: 'sessionId',
    type: AttributeType.STRING,
  },
  billingMode: BillingMode.PAY_PER_REQUEST,
  timeToLiveAttribute: 'expires',
  removalPolicy: RemovalPolicy.DESTROY, // For dev - change to RETAIN for production
  tableName: 'WestOfHauntedHouse-GameSessions',
});

/**
 * Grant Lambda function access to DynamoDB table
 * 
 * This adds IAM permissions for read/write operations.
 * Environment variables are set in the function's resource.ts file.
 */
const gameHandlerLambda = backend.gameHandler.resources.lambda;
gameSessionsTable.grantReadWriteData(gameHandlerLambda);

/**
 * Apply resource tags to all resources
 * 
 * Required tags:
 * - Project: west-of-haunted-house
 * - ManagedBy: vedfolnir
 * - Environment: dev/staging/prod
 */
// Tags are automatically applied by Amplify from amplify.yml or CLI

/**
 * Requirements Coverage:
 * - 21.1, 21.2, 21.3, 21.4: DynamoDB table with proper schema
 * - 22.7: Environment variables configured for Lambda
 * - 24.1, 24.2, 24.3: TTL, on-demand billing, proper IAM permissions
 */
