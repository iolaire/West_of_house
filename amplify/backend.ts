import { defineBackend } from '@aws-amplify/backend';
import { RemovalPolicy } from 'aws-cdk-lib';
import { AttributeType, BillingMode, Table } from 'aws-cdk-lib/aws-dynamodb';
import { 
  RestApi, 
  LambdaIntegration, 
  Cors, 
  AuthorizationType,
  MethodOptions 
} from 'aws-cdk-lib/aws-apigateway';
import { gameHandler } from './functions/game-handler/resource';

/**
 * West of Haunted House Backend Definition
 * 
 * This defines the AWS Amplify Gen 2 backend infrastructure including:
 * - DynamoDB GameSessions table (created with CDK)
 * - Lambda game handler for command processing
 * - REST API Gateway for HTTP endpoints
 * 
 * Authentication is deferred to a future phase. For MVP, the API will be publicly accessible.
 * 
 * All resources are automatically tagged with:
 * - Project: west-of-haunted-house
 * - ManagedBy: vedfolnir
 * - Environment: dev/staging/prod (from AMPLIFY_ENV)
 * 
 * Requirements: 22.4, 22.6, 24.1, 24.2, 24.3, 11.1, 11.2
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

// Get the environment name from the stack (sandbox, production, etc.)
const envName = gameHandlerStack.stackName.includes('sandbox') ? 'sandbox' : 
                gameHandlerStack.stackName.includes('production') ? 'production' : 'dev';

const gameSessionsTable = new Table(gameHandlerStack, 'GameSessions', {
  partitionKey: {
    name: 'sessionId',
    type: AttributeType.STRING,
  },
  billingMode: BillingMode.PAY_PER_REQUEST,
  timeToLiveAttribute: 'expires',
  removalPolicy: RemovalPolicy.DESTROY, // For dev - change to RETAIN for production
  tableName: `WestOfHauntedHouse-GameSessions-${envName}`,
});

/**
 * Grant Lambda function access to DynamoDB table
 * 
 * This adds IAM permissions for read/write operations.
 * Also sets the table name as an environment variable.
 */
const gameHandlerLambda = backend.gameHandler.resources.lambda;
gameSessionsTable.grantReadWriteData(gameHandlerLambda);

// Set the table name as an environment variable
gameHandlerLambda.addEnvironment('GAME_SESSIONS_TABLE_NAME', gameSessionsTable.tableName);

/**
 * Create REST API Gateway
 * 
 * This creates a REST API with endpoints for:
 * - POST /game/new - Create a new game session
 * - POST /game/command - Execute a game command
 * - GET /game/state/{session_id} - Query game state
 * 
 * CORS is enabled for all origins to support frontend development.
 * Authentication is deferred to a future phase.
 * 
 * Requirements: 11.1, 11.2
 */
const api = new RestApi(gameHandlerStack, 'GameAPI', {
  restApiName: 'West of Haunted House Game API',
  description: 'REST API for West of Haunted House text adventure game',
  deployOptions: {
    stageName: 'prod',
  },
  defaultCorsPreflightOptions: {
    allowOrigins: Cors.ALL_ORIGINS,
    allowMethods: Cors.ALL_METHODS,
    allowHeaders: ['Content-Type', 'X-Amz-Date', 'Authorization', 'X-Api-Key', 'X-Amz-Security-Token'],
  },
});

// Create Lambda integration
const lambdaIntegration = new LambdaIntegration(gameHandlerLambda);

// Method options (no authorization for MVP)
const methodOptions: MethodOptions = {
  authorizationType: AuthorizationType.NONE,
};

// Create /game resource
const gameResource = api.root.addResource('game');

// POST /game/new - Create new game session
const newGameResource = gameResource.addResource('new');
newGameResource.addMethod('POST', lambdaIntegration, methodOptions);

// POST /game/command - Execute game command
const commandResource = gameResource.addResource('command');
commandResource.addMethod('POST', lambdaIntegration, methodOptions);

// GET /game/state/{session_id} - Query game state
const stateResource = gameResource.addResource('state');
const sessionResource = stateResource.addResource('{session_id}');
sessionResource.addMethod('GET', lambdaIntegration, methodOptions);

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
 * - 11.1, 11.2: REST API with game endpoints
 * - 21.1, 21.2, 21.3, 21.4: DynamoDB table with proper schema
 * - 22.7: Environment variables configured for Lambda
 * - 24.1, 24.2, 24.3: TTL, on-demand billing, proper IAM permissions
 */
