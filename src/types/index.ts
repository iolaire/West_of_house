/**
 * Core data models and types for the Grimoire Frontend
 * Feature: grimoire-frontend
 */

// ============================================================================
// Application State
// ============================================================================

/**
 * Main application state interface
 */
export interface AppState {
  // Session
  sessionId: string | null;
  
  // Current game state
  currentRoom: string;
  roomImage: string;
  roomDescription: string;
  
  // Output history
  outputLines: OutputLine[];
  
  // UI state
  isLoading: boolean;
  isTransitioning: boolean;
  error: string | null;
  
  // Input state
  commandHistory: string[];
  historyIndex: number;
}

/**
 * Output line type for game output display
 */
export interface OutputLine {
  id: string;
  type: 'command' | 'response' | 'error';
  text: string;
  timestamp: number;
}

// ============================================================================
// API Types
// ============================================================================

/**
 * Game response from backend API
 */
export interface GameResponse {
  room: string;
  description_spooky: string;
  response_spooky: string;
  inventory?: string[];
  score?: number;
}

/**
 * Session creation response
 */
export interface SessionResponse {
  sessionId: string;
}

/**
 * Error thrown when session has expired
 */
export class SessionExpiredError extends Error {
  constructor() {
    super('Session expired. Please start a new game.');
    this.name = 'SessionExpiredError';
  }
}

/**
 * Error thrown for API failures
 */
export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

// ============================================================================
// Component Props
// ============================================================================

/**
 * Props for ImagePane component
 */
export interface ImagePaneProps {
  roomName: string;
  roomDescription: string;
  transitionDuration?: number;
}

/**
 * Props for RoomImage component
 */
export interface RoomImageProps {
  src: string;
  alt: string;
  isTransitioning: boolean;
  opacity: number;
}

/**
 * Props for GameOutput component
 */
export interface GameOutputProps {
  lines: OutputLine[];
}

/**
 * Props for CommandInput component
 */
export interface CommandInputProps {
  onSubmit: (command: string) => void;
  disabled: boolean;
}

/**
 * Props for LoadingIndicator component
 */
export interface LoadingIndicatorProps {
  isVisible: boolean;
}

/**
 * Props for AboutModal component
 */
export interface AboutModalProps {
  onClose: () => void;
}

// ============================================================================
// Context Types
// ============================================================================

/**
 * Session context value for managing game sessions
 */
export interface SessionContextValue {
  sessionId: string | null;
  createSession: () => Promise<GameResponse>;
  sendCommand: (command: string) => Promise<GameResponse>;
  isLoading: boolean;
  error: string | null;
}

// ============================================================================
// Storage Types
// ============================================================================

/**
 * Stored session data in localStorage
 */
export interface StoredSession {
  sessionId: string;
  lastAccessed: number; // timestamp
}

// ============================================================================
// Constants
// ============================================================================

/**
 * Transition duration for room image dissolve effect (3 seconds)
 */
export const TRANSITION_DURATION = 3000;

/**
 * Maximum number of output lines to keep in history
 */
export const MAX_OUTPUT_LINES = 1000;

/**
 * localStorage key for session storage
 */
export const SESSION_STORAGE_KEY = 'wohh_session';

/**
 * Default fallback image for missing room images
 */
export const DEFAULT_ROOM_IMAGE = '/images/rooms/west_of_house.png';

/**
 * API request timeout in milliseconds
 */
export const API_TIMEOUT = 30000;

/**
 * Number of retry attempts for failed API requests
 */
export const API_RETRY_ATTEMPTS = 3;

/**
 * Base delay for exponential backoff (milliseconds)
 */
export const RETRY_BASE_DELAY = 1000;
