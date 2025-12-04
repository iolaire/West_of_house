/**
 * GraphQL API Client Service
 * Feature: grimoire-frontend
 * 
 * Handles all communication with the AppSync GraphQL API for game sessions.
 * Uses Amplify Data client for type-safe GraphQL operations.
 */

import { generateClient } from 'aws-amplify/data';
import type { Schema } from '../../amplify/data/resource';
import {
  GameResponse,
  SessionExpiredError,
  ApiError,
} from '../types';

/**
 * Create Amplify Data client with type safety
 */
const client = generateClient<Schema>();

/**
 * GraphQLApiClient class for managing GraphQL API communication
 */
export class GraphQLApiClient {
  /**
   * Create a new game session
   * @returns Promise resolving to session ID and initial game state
   * @throws ApiError if the request fails
   */
  async createSession(): Promise<{ sessionId: string; initialState: GameResponse }> {
    try {
      // Generate a unique session ID
      const sessionId = crypto.randomUUID();
      
      // Calculate expiration (1 hour from now)
      const now = new Date();
      const expires = Math.floor(now.getTime() / 1000) + 3600; // Unix timestamp + 1 hour
      
      // Create new GameSession in DynamoDB via GraphQL
      const { data, errors } = await client.models.GameSession.create({
        sessionId,
        currentRoom: 'west_of_house',
        inventory: [],
        flags: JSON.stringify({}),
        roomsVisited: ['west_of_house'],
        sanity: 100,
        score: 0,
        moves: 0,
        lampBattery: 200,
        cursed: false,
        bloodMoonActive: true,
        soulsCollected: 0,
        curseDuration: 0,
        lucky: false,
        thiefHere: false,
        wonFlag: false,
        lastAccessed: now.toISOString(),
        expires,
      });

      if (errors || !data) {
        throw new ApiError(
          500,
          errors?.[0]?.message || 'Failed to create session'
        );
      }

      // Get initial room state by sending "look" command
      const initialState = await this.sendCommand(data.sessionId, 'look');

      return {
        sessionId: data.sessionId,
        initialState,
      };
    } catch (error) {
      if (error instanceof ApiError) {
        throw error;
      }
      
      const message = error instanceof Error ? error.message : 'Failed to create session';
      throw new ApiError(500, message);
    }
  }

  /**
   * Send a command to the game
   * @param sessionId - Current session ID
   * @param command - Command text to send
   * @returns Promise resolving to game response
   * @throws SessionExpiredError if session has expired
   * @throws ApiError if the request fails
   */
  async sendCommand(sessionId: string, command: string): Promise<GameResponse> {
    try {
      // Call the custom GraphQL query that invokes the Lambda function
      const { data, errors } = await client.queries.processCommand({
        sessionId,
        command,
      });

      if (errors || !data) {
        // Check if it's a session not found error
        const errorMessage = errors?.[0]?.message || 'Failed to process command';
        if (errorMessage.includes('Session not found') || errorMessage.includes('expired')) {
          throw new SessionExpiredError();
        }
        throw new ApiError(500, errorMessage);
      }

      // Map the GraphQL response to GameResponse format
      return {
        room: data.room,
        description_spooky: data.description_spooky,
        response_spooky: data.message || '',
        inventory: (data.inventory || []).filter((item): item is string => item !== null),
        score: data.score,
      };
    } catch (error) {
      if (error instanceof SessionExpiredError) {
        throw error;
      }
      
      if (error instanceof ApiError) {
        throw error;
      }
      
      const message = error instanceof Error ? error.message : 'Failed to send command';
      throw new ApiError(500, message);
    }
  }

  /**
   * Get current game state
   * @param sessionId - Session ID to retrieve
   * @returns Promise resolving to game response
   * @throws SessionExpiredError if session has expired
   * @throws ApiError if the request fails
   */
  async getGameState(sessionId: string): Promise<GameResponse> {
    try {
      const { data: session, errors } = await client.models.GameSession.get({
        sessionId,
      });

      if (errors || !session) {
        throw new SessionExpiredError();
      }

      return {
        room: session.currentRoom,
        description_spooky: 'You are standing in an open field west of a white house, with a boarded front door.',
        response_spooky: '',
        inventory: (session.inventory || []).filter((item): item is string => item !== null),
        score: session.score,
      };
    } catch (error) {
      if (error instanceof SessionExpiredError) {
        throw error;
      }
      
      const message = error instanceof Error ? error.message : 'Failed to get game state';
      throw new ApiError(500, message);
    }
  }
}

/**
 * Create a singleton instance of GraphQLApiClient
 */
export const graphQLApiClient = new GraphQLApiClient();
