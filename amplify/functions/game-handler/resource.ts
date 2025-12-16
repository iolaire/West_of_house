import { defineFunction } from '@aws-amplify/backend';

/**
 * West of Haunted House Game Handler Lambda Function
 * 
 * This Lambda function processes game commands and manages game state for the
 * West of Haunted House text adventure backend. It handles:
 * - New game creation with session management
 * - Command parsing and execution
 * - Game state persistence to DynamoDB
 * - Sanity system mechanics
 * - Room navigation and object interactions
 * 
 * Architecture:
 * - Runtime: Python 3.12 on ARM64 (Graviton2) for 20% cost savings
 * - Memory: 128MB (cost-optimized for text adventure logic)
 * - Timeout: 30 seconds (sufficient for command processing)
 * - Bundling: Python dependencies + game data JSON files
 * 
 * Environment Variables (auto-resolved by Amplify):
 * - TABLE_NAME: DynamoDB GameSessions table name
 * - AWS_REGION: AWS region for DynamoDB client
 * 
 * Requirements: 21.1, 21.2, 22.1, 22.6, 22.7, 24.1, 24.2, 24.3
 * 
 * @see https://docs.amplify.aws/react/build-a-backend/functions/custom-functions/
 */
export const gameHandler = defineFunction({
  /**
   * Function name identifier
   */
  name: 'game-handler',

  /**
   * Handler function entry point
   * Points to the handler function in index.py
   */
  entry: './index.py'
});

/**
 * Bundling Notes:
 * 
 * Amplify Gen 2 automatically bundles:
 * 1. All Python files in the function directory (*.py)
 * 2. Dependencies from requirements.txt
 * 3. All subdirectories and files (including data/ folder with JSON files)
 * 
 * The bundled package includes:
 * - index.py (Lambda handler entry point)
 * - command_parser.py
 * - game_engine.py
 * - state_manager.py
 * - sanity_system.py
 * - world_loader.py
 * - requirements.txt
 * - data/rooms_haunted.json
 * - data/objects_haunted.json
 * - data/flags_haunted.json
 * 
 * All files are now located in amplify/functions/game-handler/ for Gen 2 deployment.
 * 
 * Requirements: 20.4, 22.1
 */

/**
 * IAM Permissions (Automatically Configured):
 * 
 * 1. DynamoDB Access (configured in backend.ts):
 *    - Granted via grantReadWriteData() method
 *    - Least-privilege policy scoped to GameSession table ARN
 *    - No wildcard permissions
 * 
 * 2. CloudWatch Logs (automatically granted by Amplify):
 *    - logs:CreateLogGroup
 *    - logs:CreateLogStream
 *    - logs:PutLogEvents
 *    - Scoped to: arn:aws:logs:{region}:{account}:log-group:/aws/lambda/{function-name}:*
 * 
 * 3. Lambda Execution Role:
 *    - Amplify creates a dedicated IAM role for this function
 *    - Role name: amplify-{app-id}-{env}-gameHandler-{hash}
 *    - Follows AWS best practices for Lambda execution roles
 * 
 * All permissions follow the least-privilege principle with no wildcard resource ARNs
 * (except for CloudWatch Logs which requires :* suffix for log streams).
 * 
 * Requirements: 21.1, 21.2, 21.3, 21.4
 */

/**
 * Note: Resource tags are applied at the backend level in backend.ts
 * Required tags (automatically applied):
 * - Project: west-of-haunted-house
 * - ManagedBy: vedfolnir
 * - Environment: dev/staging/prod (from AMPLIFY_ENV)
 * 
 * Requirements: 24.1, 24.2, 24.3
 */

