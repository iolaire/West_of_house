/**
 * Property-Based Tests for SessionContext
 * Feature: grimoire-frontend, Property 12: Session Storage
 * Validates: Requirements 5.2
 * 
 * Property 12: Session Storage
 * For any newly created session, the session ID should be stored in browser localStorage
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import * as fc from 'fast-check';
import { SessionProvider, useSession } from '../contexts/SessionContext';
import { SESSION_STORAGE_KEY } from '../types';
import { ReactNode } from 'react';

describe('SessionContext Property Tests', () => {
  let originalFetch: typeof global.fetch;
  let originalLocalStorage: Storage;

  beforeEach(() => {
    // Store original fetch and localStorage
    originalFetch = global.fetch;
    originalLocalStorage = global.localStorage;

    // Clear localStorage before each test
    localStorage.clear();
    
    // Mock console methods to reduce noise
    vi.spyOn(console, 'log').mockImplementation(() => {});
    vi.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    // Restore original fetch and localStorage
    global.fetch = originalFetch;
    global.localStorage = originalLocalStorage;
    
    // Clear localStorage after each test
    localStorage.clear();
    
    vi.restoreAllMocks();
  });

  /**
   * Helper to create wrapper with SessionProvider
   */
  const createWrapper = () => {
    return ({ children }: { children: ReactNode }) => (
      <SessionProvider>{children}</SessionProvider>
    );
  };

  /**
   * Property 12: Session Storage
   * For any newly created session, the session ID should be stored in browser localStorage
   */
  it('Property 12: Session Storage - should store session ID in localStorage after creation', async () => {
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

          // Render hook with SessionProvider
          const { result } = renderHook(() => useSession(), {
            wrapper: createWrapper(),
          });

          // Create session
          await waitFor(async () => {
            await result.current.createSession();
          });

          // Wait for state to update
          await waitFor(() => {
            expect(result.current.sessionId).toBe(sessionId);
          });

          // Verify session is stored in localStorage
          const storedData = localStorage.getItem(SESSION_STORAGE_KEY);
          expect(storedData).not.toBeNull();

          if (storedData) {
            const parsed = JSON.parse(storedData);
            expect(parsed.sessionId).toBe(sessionId);
            expect(parsed.lastAccessed).toBeDefined();
            expect(typeof parsed.lastAccessed).toBe('number');
            expect(parsed.lastAccessed).toBeGreaterThan(0);
          }
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Session should be retrieved from localStorage on mount
   */
  it('should retrieve existing session from localStorage on mount', async () => {
    await fc.assert(
      fc.asyncProperty(
        fc.string({ minLength: 10, maxLength: 50 }), // sessionId
        fc.integer({ min: Date.now() - 86400000, max: Date.now() }), // lastAccessed (within last 24 hours)
        async (sessionId, lastAccessed) => {
          // Pre-populate localStorage with session
          const storedSession = {
            sessionId,
            lastAccessed,
          };
          localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(storedSession));

          // Render hook with SessionProvider
          const { result } = renderHook(() => useSession(), {
            wrapper: createWrapper(),
          });

          // Wait for session to be loaded
          await waitFor(() => {
            expect(result.current.sessionId).toBe(sessionId);
          });

          // Verify lastAccessed was updated
          const updatedData = localStorage.getItem(SESSION_STORAGE_KEY);
          expect(updatedData).not.toBeNull();

          if (updatedData) {
            const parsed = JSON.parse(updatedData);
            expect(parsed.sessionId).toBe(sessionId);
            expect(parsed.lastAccessed).toBeGreaterThanOrEqual(lastAccessed);
          }
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Session expiration should clear localStorage
   */
  it('should clear localStorage when session expires', async () => {
    await fc.assert(
      fc.asyncProperty(
        fc.string({ minLength: 10, maxLength: 50 }), // sessionId
        fc.string({ minLength: 1, maxLength: 100 }), // command
        async (sessionId, command) => {
          // Pre-populate localStorage with session
          const storedSession = {
            sessionId,
            lastAccessed: Date.now(),
          };
          localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(storedSession));

          // Mock fetch to return 404 (session expired) then fail on retry
          global.fetch = vi.fn()
            .mockResolvedValueOnce({
              ok: false,
              status: 404,
              statusText: 'Not Found',
              json: async () => ({ error: 'Session not found' }),
            } as Response)
            .mockResolvedValueOnce({
              ok: false,
              status: 500,
              statusText: 'Internal Server Error',
              json: async () => ({ error: 'Failed to create session' }),
            } as Response);

          // Render hook with SessionProvider
          const { result } = renderHook(() => useSession(), {
            wrapper: createWrapper(),
          });

          // Wait for session to be loaded
          await waitFor(() => {
            expect(result.current.sessionId).toBe(sessionId);
          }, { timeout: 1000 });

          // Try to send command (should fail with session expired)
          try {
            await result.current.sendCommand(command);
          } catch (error) {
            // Expected to throw
          }

          // Wait a bit for async operations to complete
          await new Promise(resolve => setTimeout(resolve, 100));

          // Verify localStorage was cleared (session expired removes it)
          const storedData = localStorage.getItem(SESSION_STORAGE_KEY);
          
          // Session should be cleared since auto-creation failed
          expect(storedData).toBeNull();
        }
      ),
      { numRuns: 20 } // Reduce runs to avoid timeout
    );
  }, 10000); // 10 second timeout

  /**
   * Property: lastAccessed timestamp should be updated on command
   */
  it('should update lastAccessed timestamp when sending commands', async () => {
    await fc.assert(
      fc.asyncProperty(
        fc.string({ minLength: 10, maxLength: 50 }), // sessionId
        fc.string({ minLength: 1, maxLength: 100 }), // command
        fc.record({
          room: fc.string({ minLength: 1, maxLength: 100 }),
          description_spooky: fc.string({ minLength: 1, maxLength: 500 }),
          response_spooky: fc.string({ minLength: 1, maxLength: 500 }),
        }),
        async (sessionId, command, mockResponse) => {
          // Pre-populate localStorage with session
          const initialTimestamp = Date.now() - 1000; // 1 second ago
          const storedSession = {
            sessionId,
            lastAccessed: initialTimestamp,
          };
          localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(storedSession));

          // Mock fetch to return success
          global.fetch = vi.fn().mockResolvedValue({
            ok: true,
            status: 200,
            json: async () => mockResponse,
          } as Response);

          // Render hook with SessionProvider
          const { result } = renderHook(() => useSession(), {
            wrapper: createWrapper(),
          });

          // Wait for session to be loaded
          await waitFor(() => {
            expect(result.current.sessionId).toBe(sessionId);
          }, { timeout: 1000 });

          // Ensure we have a session before sending command
          if (!result.current.sessionId) {
            throw new Error('Session not loaded');
          }

          // Send command
          const response = await result.current.sendCommand(command);
          
          // Verify response was received
          expect(response).toBeDefined();
          expect(response.room).toBe(mockResponse.room);

          // Verify lastAccessed was updated
          const updatedData = localStorage.getItem(SESSION_STORAGE_KEY);
          expect(updatedData).not.toBeNull();

          if (updatedData) {
            const parsed = JSON.parse(updatedData);
            expect(parsed.sessionId).toBe(sessionId);
            expect(parsed.lastAccessed).toBeGreaterThan(initialTimestamp);
          }
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Corrupted localStorage data should be handled gracefully
   */
  it('should handle corrupted localStorage data gracefully', async () => {
    await fc.assert(
      fc.asyncProperty(
        fc.string({ minLength: 1, maxLength: 100 }).filter(s => {
          try {
            JSON.parse(s);
            return false; // Valid JSON, skip
          } catch {
            return true; // Invalid JSON, use it
          }
        }),
        async (corruptedData) => {
          // Pre-populate localStorage with corrupted data
          localStorage.setItem(SESSION_STORAGE_KEY, corruptedData);

          // Render hook with SessionProvider
          const { result } = renderHook(() => useSession(), {
            wrapper: createWrapper(),
          });

          // Should not crash and should have no session
          await waitFor(() => {
            expect(result.current.sessionId).toBeNull();
          });

          // Corrupted data should be cleared
          const storedData = localStorage.getItem(SESSION_STORAGE_KEY);
          expect(storedData).toBeNull();
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Multiple session creations should replace previous session
   */
  it('should replace previous session when creating new session', async () => {
    await fc.assert(
      fc.asyncProperty(
        fc.string({ minLength: 10, maxLength: 50 }), // firstSessionId
        fc.string({ minLength: 10, maxLength: 50 }), // secondSessionId
        async (firstSessionId, secondSessionId) => {
          // Ensure session IDs are different
          if (firstSessionId === secondSessionId) {
            return; // Skip this test case
          }

          // Mock fetch to return first session
          global.fetch = vi.fn().mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: async () => ({ sessionId: firstSessionId }),
          } as Response);

          // Render hook with SessionProvider
          const { result } = renderHook(() => useSession(), {
            wrapper: createWrapper(),
          });

          // Create first session
          await waitFor(async () => {
            await result.current.createSession();
          });

          await waitFor(() => {
            expect(result.current.sessionId).toBe(firstSessionId);
          });

          // Verify first session is stored
          let storedData = localStorage.getItem(SESSION_STORAGE_KEY);
          expect(storedData).not.toBeNull();
          if (storedData) {
            const parsed = JSON.parse(storedData);
            expect(parsed.sessionId).toBe(firstSessionId);
          }

          // Mock fetch to return second session
          global.fetch = vi.fn().mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: async () => ({ sessionId: secondSessionId }),
          } as Response);

          // Create second session
          await waitFor(async () => {
            await result.current.createSession();
          });

          await waitFor(() => {
            expect(result.current.sessionId).toBe(secondSessionId);
          });

          // Verify second session replaced first session
          storedData = localStorage.getItem(SESSION_STORAGE_KEY);
          expect(storedData).not.toBeNull();
          if (storedData) {
            const parsed = JSON.parse(storedData);
            expect(parsed.sessionId).toBe(secondSessionId);
            expect(parsed.sessionId).not.toBe(firstSessionId);
          }
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Session storage key should be consistent
   */
  it('should always use the same storage key', async () => {
    await fc.assert(
      fc.asyncProperty(
        fc.string({ minLength: 10, maxLength: 50 }), // sessionId
        async (sessionId) => {
          // Clear localStorage before test
          localStorage.clear();

          // Mock fetch to return session response
          global.fetch = vi.fn().mockResolvedValue({
            ok: true,
            status: 200,
            json: async () => ({ sessionId }),
          } as Response);

          // Render hook with SessionProvider
          const { result } = renderHook(() => useSession(), {
            wrapper: createWrapper(),
          });

          // Create session
          await waitFor(async () => {
            await result.current.createSession();
          }, { timeout: 1000 });

          await waitFor(() => {
            expect(result.current.sessionId).toBe(sessionId);
          }, { timeout: 1000 });

          // Verify the exact key is used
          const storedData = localStorage.getItem(SESSION_STORAGE_KEY);
          expect(storedData).not.toBeNull();

          if (storedData) {
            const parsed = JSON.parse(storedData);
            expect(parsed.sessionId).toBe(sessionId);
          }

          // Verify the key exists in localStorage
          // Note: We can't check Object.keys(localStorage) because our mock
          // exposes the internal 'store' property. Instead, we verify the key directly.
          expect(localStorage.getItem(SESSION_STORAGE_KEY)).not.toBeNull();
          
          // Verify we can retrieve it
          const retrieved = localStorage.getItem(SESSION_STORAGE_KEY);
          expect(retrieved).toBe(storedData);
        }
      ),
      { numRuns: 100 }
    );
  });
});
