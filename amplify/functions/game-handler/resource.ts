import { execSync } from 'child_process';
import * as path from 'path';
import { fileURLToPath } from 'url';
import { defineFunction } from '@aws-amplify/backend';
import { DockerImage, Duration } from 'aws-cdk-lib';
import { Code, Function, Runtime, Architecture } from 'aws-cdk-lib/aws-lambda';

const functionDir = path.dirname(fileURLToPath(import.meta.url));

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
export const gameHandler = defineFunction(
  (scope) =>
    new Function(scope, 'game-handler', {
      /**
       * Handler function entry point
       * Points to the handler function in index.py
       */
      handler: 'index.handler',
      
      /**
       * Runtime: Python 3.12
       * Using the latest stable Python runtime for Lambda
       */
      runtime: Runtime.PYTHON_3_12,
      
      /**
       * Architecture: ARM64 for Graviton2 processors
       * Provides 20% better price-performance compared to x86_64
       * 
       * Requirements: 22.1, 22.7
       */
      architecture: Architecture.ARM_64,
      
      /**
       * Resource allocation
       * - 128MB memory: Sufficient for text adventure logic, minimizes cost
       * - 30 seconds timeout: Allows for command processing and DynamoDB operations
       * 
       * Requirements: 22.1, 22.2
       */
      memorySize: 128,
      timeout: Duration.seconds(30),
      
      /**
       * Code bundling configuration
       * Bundles Python code, dependencies, and game data files
       */
      code: Code.fromAsset(functionDir, {
        bundling: {
          image: DockerImage.fromRegistry('dummy'),
          local: {
            tryBundle(outputDir: string) {
              // Install Python dependencies for ARM64 architecture
              execSync(
                `python3 -m pip install -r ${path.join(functionDir, 'requirements.txt')} -t ${outputDir} --platform manylinux2014_aarch64 --only-binary=:all:`,
                { stdio: 'inherit' }
              );
              
              // Copy all Python files and data directory
              execSync(`cp -r ${functionDir}/*.py ${outputDir}/`, { stdio: 'inherit' });
              execSync(`cp -r ${functionDir}/data ${outputDir}/`, { stdio: 'inherit' });
              
              return true;
            },
          },
        },
      }),
      
      /**
       * Environment variables
       * 
       * GAME_SESSIONS_TABLE_NAME: DynamoDB table name for game sessions
       * This must match the table name created in backend.ts
       * 
       * Requirements: 22.7
       */
      environment: {
        GAME_SESSIONS_TABLE_NAME: 'WestOfHauntedHouse-GameSessions',
      },
    }),
  {
    /**
     * Resource group name for organizing related resources
     * Groups this function with data resources
     */
    resourceGroupName: 'data',
  }
);

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
