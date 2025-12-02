# Amplify Gen 2 Migration Plan

## Overview

This document outlines the migration from AWS Amplify Gen 1 (CLI-based) to Gen 2 (TypeScript code-first) for the West of Haunted House game backend.

## Why Migrate to Gen 2?

### Problems with Gen 1
1. **Environment Variable Resolution Issues**: Gen 1 CLI has difficulty resolving environment variables from dependent resources (DynamoDB → Lambda)
2. **Manual Configuration**: Requires interactive prompts that are hard to automate
3. **CloudFormation Complexity**: Difficult to debug when deployments fail
4. **Limited Type Safety**: JSON-based configuration prone to errors

### Benefits of Gen 2
1. **Code-First Infrastructure**: Define infrastructure in TypeScript with full type safety
2. **Automatic Dependency Resolution**: Environment variables automatically resolved from resource outputs
3. **Better Developer Experience**: Local sandbox environments for testing
4. **Modern Tooling**: Built on AWS CDK with full CDK capabilities
5. **Future-Proof**: Recommended approach for all new Amplify projects

## Migration Strategy

### Phase 1: Documentation Updates ✅
- [x] Update `.kiro/steering/tech.md` with Gen 2 requirements
- [x] Update `.kiro/steering/structure.md` with Gen 2 project structure
- [x] Update `.kiro/specs/game-backend-api/requirements.md` with Gen 2 acceptance criteria
- [x] Update `.kiro/specs/game-backend-api/design.md` with Gen 2 deployment guide
- [x] Add Gen 2 migration tasks to `.kiro/specs/game-backend-api/tasks.md`

### Phase 2: Gen 2 Project Setup (Task 17.3.1)
- [ ] Run `npm create amplify@latest`
- [ ] Initialize TypeScript configuration
- [ ] Create `amplify/backend.ts` entry point
- [ ] Install dependencies

### Phase 3: Define Infrastructure (Tasks 17.3.2-17.3.6)
- [ ] Define DynamoDB table in `amplify/data/resource.ts`
- [ ] Define Lambda function in `amplify/functions/game-handler/resource.ts`
- [ ] Migrate Python code to Gen 2 structure
- [ ] Define API Gateway endpoints in `backend.ts`
- [ ] Configure IAM permissions

### Phase 4: Testing & Deployment (Tasks 17.3.7-17.3.8)
- [ ] Test with local sandbox (`npx ampx sandbox`)
- [ ] Deploy to AWS via Git push
- [ ] Verify all resources created correctly

### Phase 5: Verification (Task 17.4)
- [ ] Verify Lambda ARM64 architecture
- [ ] Verify DynamoDB TTL enabled
- [ ] Verify API Gateway endpoints accessible
- [ ] Verify resource tags applied

## Key Differences: Gen 1 vs Gen 2

| Aspect | Gen 1 | Gen 2 |
|--------|-------|-------|
| **Configuration** | CLI commands + JSON | TypeScript code |
| **Infrastructure** | CloudFormation templates | AWS CDK |
| **Environment Variables** | Manual SSM parameters | Auto-resolved from outputs |
| **Local Testing** | Limited | Full sandbox environment |
| **Type Safety** | None | Full TypeScript support |
| **Deployment** | `amplify push` | Git push or `npx ampx pipeline-deploy` |

## Gen 2 Project Structure

```
amplify/
├── backend.ts                    # Main entry point
├── data/
│   └── resource.ts               # DynamoDB tables
├── functions/
│   └── game-handler/
│       ├── resource.ts           # Lambda definition (TypeScript)
│       ├── handler.py            # Lambda code (Python)
│       ├── requirements.txt      # Python dependencies
│       └── data/                 # Game data files
└── package.json                  # Node.js dependencies
```

## Code Examples

### DynamoDB Table Definition (Gen 2)

```typescript
// amplify/data/resource.ts
import { type ClientSchema, a, defineData } from '@aws-amplify/backend';

const schema = a.schema({
  GameSession: a.customType({
    sessionId: a.string().required(),
    currentRoom: a.string().required(),
    inventory: a.string().array(),
    flags: a.json(),
    sanity: a.integer(),
    score: a.integer(),
    moves: a.integer(),
    lampBattery: a.integer(),
    ttl: a.integer()
  })
});

export type Schema = ClientSchema<typeof schema>;

export const data = defineData({
  schema,
  authorizationModes: {
    defaultAuthorizationMode: 'iam'
  }
});
```

### Lambda Function Definition (Gen 2)

```typescript
// amplify/functions/game-handler/resource.ts
import { defineFunction } from '@aws-amplify/backend';
import { Code, Function, Runtime, Architecture } from 'aws-cdk-lib/aws-lambda';
import { Duration } from 'aws-cdk-lib';

export const gameHandler = defineFunction(
  (scope) =>
    new Function(scope, 'game-handler', {
      handler: 'index.handler',
      runtime: Runtime.PYTHON_3_12,
      architecture: Architecture.ARM_64,
      timeout: Duration.seconds(30),
      memorySize: 128,
      code: Code.fromAsset(__dirname, {
        bundling: {
          // Python bundling configuration
        }
      })
    }),
  {
    resourceGroupName: 'api'
  }
);
```

### Backend Definition (Gen 2)

```typescript
// amplify/backend.ts
import { defineBackend } from '@aws-amplify/backend';
import { gameHandler } from './functions/game-handler/resource';
import { data } from './data/resource';

const backend = defineBackend({
  gameHandler,
  data
});

// Grant Lambda access to DynamoDB
backend.data.resources.tables.GameSessions.grantReadWriteData(
  backend.gameHandler.resources.lambda
);

// Add API Gateway (simplified)
// Full API Gateway configuration would go here
```

## Migration Checklist

- [x] Update documentation with Gen 2 requirements
- [x] Update steering documents
- [x] Update requirements with Gen 2 acceptance criteria
- [x] Update design document with Gen 2 deployment guide
- [x] Add Gen 2 migration tasks to task list
- [ ] Execute migration tasks (17.3.1 - 17.3.8)
- [ ] Verify deployment (17.4)
- [ ] Test deployed API (17.5)

## Resources

- [Amplify Gen 2 Documentation](https://docs.amplify.aws/javascript/)
- [Gen 1 to Gen 2 Migration Guide](https://docs.amplify.aws/javascript/start/migrate-to-gen2/)
- [Custom Functions (Python)](https://docs.amplify.aws/javascript/build-a-backend/functions/custom-functions/)
- [AWS CDK Documentation](https://docs.aws.amazon.com/cdk/latest/guide/home.html)

## Next Steps

1. Begin with task 17.3.1: Create new Gen 2 project structure
2. Follow tasks sequentially through 17.3.8
3. Test thoroughly with local sandbox before deploying
4. Deploy to AWS and verify all resources
5. Update any remaining Gen 1 references in codebase

## Notes

- All existing Python Lambda code can be reused without changes
- Game data JSON files remain unchanged
- Tests remain unchanged
- Only infrastructure definition changes from CLI to TypeScript
- Gen 2 resolves the environment variable issues we encountered with Gen 1
