/**
 * GrimoireContainer Component
 * Feature: grimoire-frontend
 * 
 * Main layout container with book-like structure:
 * - Two-column grid layout (image left, text right)
 * - Manages overall game state
 * - Coordinates image transitions with text updates
 * - Handles responsive layout for narrow viewports
 * - Integrates ImagePane, GameOutput, CommandInput, LoadingIndicator
 * 
 * Requirements: 1.2, 1.3, 1.5, 10.1, 10.5
 */

import React, { useState, useCallback, useEffect } from 'react';
import { OutputLine, GameResponse } from '../types';
import { useSession } from '../contexts/SessionContext';
import ImagePane from './ImagePane';
import GameOutput from './GameOutput';
import CommandInput from './CommandInput';
import LoadingIndicator from './LoadingIndicator';
import '../styles/GrimoireContainer.css';

/**
 * GrimoireContainer component
 * 
 * Main container that orchestrates the grimoire interface
 * Requirement 1.2: Show current room image on the left page
 * Requirement 1.3: Show game text and command input on the right page
 * Requirement 1.5: Adapt to responsive 2D layout for small viewports
 * Requirement 10.1: Use clean, book-like layout
 * Requirement 10.5: Stack image above text in single-column layout for narrow viewports
 */
const GrimoireContainer: React.FC = () => {
  // Session context
  const { sessionId, createSession, sendCommand, isLoading, error: sessionError } = useSession();
  
  // Game state
  const [currentRoom, setCurrentRoom] = useState<string>('West of House');
  const [roomDescription, setRoomDescription] = useState<string>('You are standing in an open field west of a white house, with a boarded front door.');
  const [outputLines, setOutputLines] = useState<OutputLine[]>([]);
  const [error, setError] = useState<string | null>(null);

  /**
   * Initialize session on mount
   * Requirement 5.1: Create new session on first load
   */
  useEffect(() => {
    const initializeSession = async () => {
      if (!sessionId) {
        try {
          await createSession();
          
          // Add welcome message to output
          const welcomeLine: OutputLine = {
            id: `welcome-${Date.now()}`,
            type: 'response',
            text: 'Welcome to West of Haunted House. The grimoire opens before you...',
            timestamp: Date.now(),
          };
          
          setOutputLines([welcomeLine]);
        } catch (err) {
          console.error('Failed to initialize session:', err);
          setError('Failed to start game. Please refresh the page.');
        }
      }
    };

    initializeSession();
  }, [sessionId, createSession]);

  /**
   * Handle command submission
   * Requirements: 3.1, 3.2, 4.1, 4.2, 7.2, 12.1, 12.2
   */
  const handleCommandSubmit = useCallback(async (command: string) => {
    if (!sessionId) {
      setError('No active session. Please refresh the page.');
      return;
    }

    // Clear any previous errors
    setError(null);

    // Add command to output (Requirement 4.1)
    const commandLine: OutputLine = {
      id: `cmd-${Date.now()}`,
      type: 'command',
      text: command,
      timestamp: Date.now(),
    };
    
    setOutputLines(prev => [...prev, commandLine]);

    try {
      // Send command to backend (Requirement 3.1)
      const response: GameResponse = await sendCommand(command);
      
      // Update room state if room changed
      if (response.room && response.room !== currentRoom) {
        setCurrentRoom(response.room);
      }
      
      // Update room description (Requirement 12.1: use description_spooky)
      if (response.description_spooky) {
        setRoomDescription(response.description_spooky);
      }
      
      // Add response to output (Requirement 4.2, 12.2: use response_spooky)
      const responseLine: OutputLine = {
        id: `resp-${Date.now()}`,
        type: 'response',
        text: response.response_spooky || response.description_spooky,
        timestamp: Date.now(),
      };
      
      setOutputLines(prev => [...prev, responseLine]);
      
    } catch (err) {
      // Handle errors (Requirement 7.2)
      const errorMessage = err instanceof Error ? err.message : 'An error occurred';
      
      const errorLine: OutputLine = {
        id: `err-${Date.now()}`,
        type: 'error',
        text: errorMessage,
        timestamp: Date.now(),
      };
      
      setOutputLines(prev => [...prev, errorLine]);
      setError(errorMessage);
    }
  }, [sessionId, sendCommand, currentRoom]);

  /**
   * Display session errors in output
   */
  useEffect(() => {
    if (sessionError) {
      const errorLine: OutputLine = {
        id: `session-err-${Date.now()}`,
        type: 'error',
        text: sessionError,
        timestamp: Date.now(),
      };
      
      setOutputLines(prev => [...prev, errorLine]);
    }
  }, [sessionError]);

  return (
    <div className="grimoire-container">
      {/* Left page: Room image (Requirement 1.2) */}
      <div className="grimoire-page grimoire-page--left">
        <ImagePane
          roomName={currentRoom}
          roomDescription={roomDescription}
        />
      </div>

      {/* Right page: Game text and input (Requirement 1.3) */}
      <div className="grimoire-page grimoire-page--right">
        <div className="text-pane">
          {/* Game output area */}
          <GameOutput lines={outputLines} />
          
          {/* Command input and loading indicator */}
          <div className="input-area">
            <CommandInput
              onSubmit={handleCommandSubmit}
              disabled={isLoading}
            />
            <LoadingIndicator isVisible={isLoading} />
          </div>
          
          {/* Error display */}
          {error && (
            <div className="error-message" role="alert">
              {error}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default GrimoireContainer;
