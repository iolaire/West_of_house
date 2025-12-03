/**
 * Game API Client Service
 * Feature: grimoire-frontend
 * 
 * Handles all communication with the backend API for game sessions and commands.
 * Implements error handling for network errors, session expiration, and API errors.
 */

import {
  GameResponse,
  SessionResponse,
  SessionExpiredError,
  ApiError,
  API_TIMEOUT,
  API_RETRY_ATTEMPTS,
  RETRY_BASE_DELAY,
} from '../types';
import { getApiBaseUrl, getApiTimeout } from '../config';

/**
 * GameApiClient class for managing API communication
 */
export class GameApiClient {
  private baseUrl: string;
  private timeout: number;

  /**
   * Create a new GameApiClient instance
   * @param baseUrl - Base URL for the API (optional, defaults to config)
   * @param timeout - Request timeout in milliseconds (optional, defaults to config)
   */
  constructor(baseUrl?: string, timeout?: number) {
    this.baseUrl = baseUrl || getApiBaseUrl();
    this.timeout = timeout || getApiTimeout();
  }

  /**
   * Create a new game session
   * @returns Promise resolving to session ID
   * @throws ApiError if the request fails
   */
  async createSession(): Promise<string> {
    const response = await this.fetchWithTimeout(
      `${this.baseUrl}/game`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({}),
      }
    );

    const data = await this.handleResponse<SessionResponse>(response);
    return data.sessionId;
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
    const response = await this.fetchWithTimeout(
      `${this.baseUrl}/game`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          sessionId,
          command,
        }),
      }
    );

    return this.handleResponse<GameResponse>(response);
  }

  /**
   * Fetch with timeout support
   * @param url - URL to fetch
   * @param options - Fetch options
   * @returns Promise resolving to Response
   * @throws ApiError if timeout occurs or network error
   */
  private async fetchWithTimeout(
    url: string,
    options: RequestInit
  ): Promise<Response> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    try {
      const response = await fetch(url, {
        ...options,
        signal: controller.signal,
      });
      clearTimeout(timeoutId);
      return response;
    } catch (error) {
      clearTimeout(timeoutId);
      
      if (error instanceof Error) {
        if (error.name === 'AbortError') {
          throw new ApiError(
            408,
            `Request timeout after ${this.timeout}ms`
          );
        }
        
        // Network error
        throw new ApiError(
          0,
          'Network error. Please check your internet connection and try again.'
        );
      }
      
      throw new ApiError(0, 'An unexpected error occurred');
    }
  }

  /**
   * Handle API response and parse JSON
   * @param response - Fetch Response object
   * @returns Promise resolving to parsed response data
   * @throws SessionExpiredError if session has expired (404)
   * @throws ApiError for other error statuses
   */
  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      // Session expired
      if (response.status === 404) {
        throw new SessionExpiredError();
      }

      // Try to get error message from response
      let errorMessage = `API error: ${response.status} ${response.statusText}`;
      try {
        const errorData = await response.json();
        if (errorData.message) {
          errorMessage = errorData.message;
        } else if (errorData.error) {
          errorMessage = errorData.error;
        }
      } catch {
        // If JSON parsing fails, use default error message
        try {
          const textError = await response.text();
          if (textError) {
            errorMessage = textError;
          }
        } catch {
          // Use default error message
        }
      }

      throw new ApiError(response.status, errorMessage);
    }

    try {
      const data = await response.json();
      return data as T;
    } catch (error) {
      throw new ApiError(
        500,
        'Failed to parse API response. Invalid JSON format.'
      );
    }
  }

  /**
   * Retry a request with exponential backoff
   * @param fn - Function to retry
   * @param attempts - Number of retry attempts
   * @returns Promise resolving to function result
   */
  async retryWithBackoff<T>(
    fn: () => Promise<T>,
    attempts: number = API_RETRY_ATTEMPTS
  ): Promise<T> {
    let lastError: Error | null = null;

    for (let i = 0; i < attempts; i++) {
      try {
        return await fn();
      } catch (error) {
        lastError = error as Error;

        // Don't retry on session expired or client errors (4xx)
        if (error instanceof SessionExpiredError) {
          throw error;
        }
        if (error instanceof ApiError && error.status >= 400 && error.status < 500) {
          throw error;
        }

        // Last attempt, throw error
        if (i === attempts - 1) {
          throw error;
        }

        // Wait before retrying (exponential backoff)
        const delay = RETRY_BASE_DELAY * Math.pow(2, i);
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }

    throw lastError || new Error('Retry failed');
  }
}

/**
 * Create a singleton instance of GameApiClient
 */
export const gameApiClient = new GameApiClient();
