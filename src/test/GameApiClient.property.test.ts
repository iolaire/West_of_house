/**
 * Property-Based Tests for GameApiClient
 * Feature: grimoire-frontend, Property 18: Response Parsing
 * Validates: Requirements 9.2
 * 
 * Property 18: Response Parsing
 * For any valid backend response, the grimoire should successfully parse and extract 
 * the room name, description_spooky, and response_spooky fields
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import * as fc from 'fast-check';
import { GameApiClient } from '../services/GameApiClient';
import { GameResponse, SessionExpiredError, ApiError } from '../types';

describe('GameApiClient Property Tests', () => {
  let apiClient: GameApiClient;
  let originalFetch: typeof global.fetch;

  beforeEach(() => {
    // Store original fetch
    originalFetch = global.fetch;
    
    // Create API client with test URL
    apiClient = new GameApiClient('http://test-api.example.com', 5000);
  });

  afterEach(() => {
    // Restore original fetch
    global.fetch = originalFetch;
    vi.restoreAllMocks();
  });

  /**
   * Property 18: Response Parsing
   * For any valid backend response, the grimoire should successfully parse and extract
   * the room name, description_spooky, and response_spooky fields
   */
  it('Property 18: Response Parsing - should parse valid game responses correctly', async () => {
    await fc.assert(
      fc.asyncProperty(
        // Generate arbitrary valid game responses
        fc.record({
          room: fc.string({ minLength: 1, maxLength: 100 }),
          description_spooky: fc.string({ minLength: 1, maxLength: 500 }),
          response_spooky: fc.string({ minLength: 1, maxLength: 500 }),
          inventory: fc.option(fc.array(fc.string({ minLength: 1, maxLength: 50 })), { nil: undefined }),
          score: fc.option(fc.integer({ min: 0, max: 1000 }), { nil: undefined }),
        }),
        fc.string({ minLength: 1, maxLength: 50 }), // sessionId
        fc.string({ minLength: 1, maxLength: 100 }), // command
        async (mockResponse, sessionId, command) => {
          // Mock fetch to return the generated response
          global.fetch = vi.fn().mockResolvedValue({
            ok: true,
            status: 200,
            json: async () => mockResponse,
          } as Response);

          // Send command
          const result = await apiClient.sendCommand(sessionId, command);

          // Verify all required fields are present and match
          expect(result.room).toBe(mockResponse.room);
          expect(result.description_spooky).toBe(mockResponse.description_spooky);
          expect(result.response_spooky).toBe(mockResponse.response_spooky);

          // Verify optional fields if present
          if (mockResponse.inventory !== undefined) {
            expect(result.inventory).toEqual(mockResponse.inventory);
          }
          if (mockResponse.score !== undefined) {
            expect(result.score).toBe(mockResponse.score);
          }
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Session creation should return a valid session ID
   */
  it('should create session and return valid session ID', async () => {
    await fc.assert(
      fc.asyncProperty(
        fc.string({ minLength: 10, maxLength: 50 }), // sessionId
        async (sessionId) => {
          // Mock fetch to return session response
          global.fetch = vi.fn().mockResolvedValue({
            ok: true,
            status: 200,
            json: async () => ({ sessionId }),
          } as Response);

          const result = await apiClient.createSession();

          expect(result).toBe(sessionId);
          expect(typeof result).toBe('string');
          expect(result.length).toBeGreaterThan(0);
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property: 404 responses should throw SessionExpiredError
   */
  it('should throw SessionExpiredError for 404 responses', async () => {
    await fc.assert(
      fc.asyncProperty(
        fc.string({ minLength: 1, maxLength: 50 }), // sessionId
        fc.string({ minLength: 1, maxLength: 100 }), // command
        async (sessionId, command) => {
          // Mock fetch to return 404
          global.fetch = vi.fn().mockResolvedValue({
            ok: false,
            status: 404,
            statusText: 'Not Found',
            json: async () => ({ error: 'Session not found' }),
          } as Response);

          await expect(apiClient.sendCommand(sessionId, command))
            .rejects
            .toThrow(SessionExpiredError);
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Non-404 error responses should throw ApiError with correct status
   */
  it('should throw ApiError for non-404 error responses', async () => {
    await fc.assert(
      fc.asyncProperty(
        fc.integer({ min: 400, max: 599 }).filter(status => status !== 404), // error status codes except 404
        fc.string({ minLength: 1, maxLength: 50 }), // sessionId
        fc.string({ minLength: 1, maxLength: 100 }), // command
        async (errorStatus, sessionId, command) => {
          // Mock fetch to return error
          global.fetch = vi.fn().mockResolvedValue({
            ok: false,
            status: errorStatus,
            statusText: 'Error',
            json: async () => ({ error: 'Test error' }),
          } as Response);

          try {
            await apiClient.sendCommand(sessionId, command);
            // Should not reach here
            expect(true).toBe(false);
          } catch (error) {
            expect(error).toBeInstanceOf(ApiError);
            expect((error as ApiError).status).toBe(errorStatus);
          }
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Network errors should throw ApiError with status 0
   */
  it('should throw ApiError for network errors', async () => {
    await fc.assert(
      fc.asyncProperty(
        fc.string({ minLength: 1, maxLength: 50 }), // sessionId
        fc.string({ minLength: 1, maxLength: 100 }), // command
        async (sessionId, command) => {
          // Mock fetch to throw network error
          global.fetch = vi.fn().mockRejectedValue(new TypeError('Network error'));

          try {
            await apiClient.sendCommand(sessionId, command);
            // Should not reach here
            expect(true).toBe(false);
          } catch (error) {
            expect(error).toBeInstanceOf(ApiError);
            expect((error as ApiError).status).toBe(0);
            expect((error as ApiError).message).toContain('Network error');
          }
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Timeout should throw ApiError with status 408
   */
  it('should throw ApiError for timeout', async () => {
    await fc.assert(
      fc.asyncProperty(
        fc.string({ minLength: 1, maxLength: 50 }), // sessionId
        fc.string({ minLength: 1, maxLength: 100 }), // command
        async (sessionId, command) => {
          // Mock fetch to throw abort error (timeout)
          const abortError = new Error('The operation was aborted');
          abortError.name = 'AbortError';
          global.fetch = vi.fn().mockRejectedValue(abortError);

          try {
            await apiClient.sendCommand(sessionId, command);
            // Should not reach here
            expect(true).toBe(false);
          } catch (error) {
            expect(error).toBeInstanceOf(ApiError);
            expect((error as ApiError).status).toBe(408);
            expect((error as ApiError).message).toContain('timeout');
          }
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Invalid JSON responses should throw ApiError
   */
  it('should throw ApiError for invalid JSON responses', async () => {
    await fc.assert(
      fc.asyncProperty(
        fc.string({ minLength: 1, maxLength: 50 }), // sessionId
        fc.string({ minLength: 1, maxLength: 100 }), // command
        async (sessionId, command) => {
          // Mock fetch to return invalid JSON
          global.fetch = vi.fn().mockResolvedValue({
            ok: true,
            status: 200,
            json: async () => {
              throw new SyntaxError('Invalid JSON');
            },
          } as Response);

          try {
            await apiClient.sendCommand(sessionId, command);
            // Should not reach here
            expect(true).toBe(false);
          } catch (error) {
            expect(error).toBeInstanceOf(ApiError);
            expect((error as ApiError).status).toBe(500);
            expect((error as ApiError).message).toContain('parse');
          }
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Response with missing required fields should still parse
   * (The API client should return what it receives, validation happens elsewhere)
   */
  it('should parse responses even with missing optional fields', async () => {
    await fc.assert(
      fc.asyncProperty(
        fc.record({
          room: fc.string({ minLength: 1, maxLength: 100 }),
          description_spooky: fc.string({ minLength: 1, maxLength: 500 }),
          response_spooky: fc.string({ minLength: 1, maxLength: 500 }),
          // No inventory or score
        }),
        fc.string({ minLength: 1, maxLength: 50 }), // sessionId
        fc.string({ minLength: 1, maxLength: 100 }), // command
        async (mockResponse, sessionId, command) => {
          // Mock fetch to return minimal response
          global.fetch = vi.fn().mockResolvedValue({
            ok: true,
            status: 200,
            json: async () => mockResponse,
          } as Response);

          const result = await apiClient.sendCommand(sessionId, command);

          // Required fields should be present
          expect(result.room).toBe(mockResponse.room);
          expect(result.description_spooky).toBe(mockResponse.description_spooky);
          expect(result.response_spooky).toBe(mockResponse.response_spooky);

          // Optional fields should be undefined
          expect(result.inventory).toBeUndefined();
          expect(result.score).toBeUndefined();
        }
      ),
      { numRuns: 100 }
    );
  });
});

