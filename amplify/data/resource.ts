import { type ClientSchema, a, defineData } from '@aws-amplify/backend';

/**
 * GameSessions DynamoDB Table Schema
 * 
 * This table stores game session state for the West of Haunted House backend.
 * Each session represents a unique game instance with persistent state across
 * multiple API requests.
 * 
 * Features:
 * - TTL-based automatic cleanup (sessions expire after 1 hour of inactivity)
 * - On-demand billing mode for cost optimization
 * - Guest authorization (no authentication required for MVP)
 * 
 * Requirements: 22.3, 24.1, 24.2, 24.3
 */
const schema = a.schema({
  GameSession: a
    .model({
      // Primary key - unique session identifier
      sessionId: a.id().required(),
      
      // Game state fields
      currentRoom: a.string().required(),
      inventory: a.string().array(), // Array of object IDs
      flags: a.json(), // Game flags as JSON object
      roomsVisited: a.string().array(), // Set of visited room IDs
      
      // Player statistics
      sanity: a.integer().required().default(100), // 0-100
      score: a.integer().required().default(0),
      moves: a.integer().required().default(0),
      lampBattery: a.integer().required().default(200),
      
      // Halloween mechanics (MVP includes sanity only)
      cursed: a.boolean().default(false),
      bloodMoonActive: a.boolean().default(true),
      soulsCollected: a.integer().default(0),
      curseDuration: a.integer().default(0),
      
      // Original Zork state
      lucky: a.boolean().default(false),
      thiefHere: a.boolean().default(false),
      wonFlag: a.boolean().default(false),
      
      // Session management
      lastAccessed: a.datetime().required(),
      expires: a.integer().required(), // Unix timestamp for TTL
      
      // Metadata
      createdAt: a.datetime(),
      updatedAt: a.datetime(),
    })
    .authorization((allow) => [
      // Allow guest access for MVP (no authentication required)
      allow.guest(),
    ]),
});

export type Schema = ClientSchema<typeof schema>;

/**
 * Define the data backend with GameSessions table
 * 
 * Configuration:
 * - On-demand billing mode (pay per request)
 * - TTL enabled on 'expires' field for automatic cleanup
 * - Guest authorization for MVP (authentication deferred to future phase)
 */
export const data = defineData({
  schema,
  authorizationModes: {
    defaultAuthorizationMode: 'identityPool',
  },
});

/**
 * Note: Resource tags are applied at the backend level in backend.ts
 * Required tags:
 * - Project: west-of-haunted-house
 * - ManagedBy: vedfolnir
 * - Environment: dev/staging/prod
 */
