/**
 * Session Context Provider
 * Feature: grimoire-frontend
 * 
 * Manages game session lifecycle including:
 * - Session creation and storage in localStorage
 * - Session retrieval on app load
 * - Session expiration detection
 * - API communication for commands
 * 
 * Requirements: 5.1, 5.2, 5.3, 5.4, 5.5
 */

import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import {
  SessionContextValue,
  GameResponse,
  StoredSession,
  SESSION_STORAGE_KEY,
  SessionExpiredError,
  ApiError,
} from '../types';
import { gameApiClient } from '../services';

/**
 * Session Context
 */
const SessionContext = createContext<SessionContextValue | undefined>(undefined);

/**
 * Props for SessionProvider component
 */
interface SessionProviderProps {
  children: ReactNode;
}

/**
 * SessionProvider component
 * 
 * Provides session management functionality to all child components.
 * Handles session creation, storage, retrieval, and expiration.
 */
export const SessionProvider: React.FC<SessionProviderProps> = ({ children }) => {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * Load session from localStorage on mount
   * Requirement 5.3: Retrieve session ID from localStorage and restore game state
   */
  useEffect(() => {
    const loadSession = () => {
      try {
        const storedData = localStorage.getItem(SESSION_STORAGE_KEY);
        
        if (storedData) {
          const stored: StoredSession = JSON.parse(storedData);
          
          // Update last accessed timestamp
          const updatedSession: StoredSession = {
            ...stored,
            lastAccessed: Date.now(),
          };
          
          localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(updatedSession));
          setSessionId(stored.sessionId);
          
          console.log('Session restored from localStorage:', stored.sessionId);
        } else {
          console.log('No existing session found in localStorage');
        }
      } catch (error) {
        console.error('Failed to load session from localStorage:', error);
        // Clear corrupted data
        localStorage.removeItem(SESSION_STORAGE_KEY);
      }
    };

    loadSession();
  }, []);

  /**
   * Create a new game session
   * Requirements: 5.1, 5.2, 5.4
   */
  const createSession = useCallback(async (): Promise<void> => {
    setIsLoading(true);
    setError(null);

    try {
      // Call API to create new session
      const newSessionId = await gameApiClient.createSession();
      
      // Store session in state
      setSessionId(newSessionId);
      
      // Store session in localStorage (Requirement 5.2)
      const sessionData: StoredSession = {
        sessionId: newSessionId,
        lastAccessed: Date.now(),
      };
      
      localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(sessionData));
      
      console.log('New session created:', newSessionId);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to create session';
      setError(errorMessage);
      console.error('Session creation failed:', err);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Send a command to the game
   * Requirements: 5.5 (session expiration detection)
   */
  const sendCommand = useCallback(async (command: string): Promise<GameResponse> => {
    if (!sessionId) {
      throw new Error('No active session. Please create a session first.');
    }

    setIsLoading(true);
    setError(null);

    try {
      // Send command to API
      const response = await gameApiClient.sendCommand(sessionId, command);
      
      // Update last accessed timestamp
      const storedData = localStorage.getItem(SESSION_STORAGE_KEY);
      if (storedData) {
        const stored: StoredSession = JSON.parse(storedData);
        const updatedSession: StoredSession = {
          ...stored,
          lastAccessed: Date.now(),
        };
        localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(updatedSession));
      }
      
      return response;
    } catch (err) {
      // Handle session expiration (Requirement 5.5)
      if (err instanceof SessionExpiredError) {
        console.log('Session expired, clearing localStorage');
        
        // Clear expired session from localStorage
        localStorage.removeItem(SESSION_STORAGE_KEY);
        setSessionId(null);
        
        const errorMessage = 'Your session has expired. Starting a new game...';
        setError(errorMessage);
        
        // Automatically create a new session
        try {
          await createSession();
          // Retry the command with the new session
          if (sessionId) {
            return await gameApiClient.sendCommand(sessionId, command);
          }
        } catch (retryErr) {
          console.error('Failed to create new session after expiration:', retryErr);
        }
        
        throw new Error(errorMessage);
      }
      
      // Handle other API errors
      if (err instanceof ApiError) {
        const errorMessage = `API Error: ${err.message}`;
        setError(errorMessage);
        throw err;
      }
      
      // Handle generic errors
      const errorMessage = err instanceof Error ? err.message : 'Failed to send command';
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [sessionId, createSession]);

  const contextValue: SessionContextValue = {
    sessionId,
    createSession,
    sendCommand,
    isLoading,
    error,
  };

  return (
    <SessionContext.Provider value={contextValue}>
      {children}
    </SessionContext.Provider>
  );
};

/**
 * Hook to use session context
 * 
 * @throws Error if used outside of SessionProvider
 */
export const useSession = (): SessionContextValue => {
  const context = useContext(SessionContext);
  
  if (context === undefined) {
    throw new Error('useSession must be used within a SessionProvider');
  }
  
  return context;
};

/**
 * Export SessionContext for testing purposes
 */
export { SessionContext };
