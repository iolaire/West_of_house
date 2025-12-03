/**
 * CommandInput Component
 * Feature: grimoire-frontend
 * 
 * Text input field for player commands with:
 * - Enter key submission
 * - Command history navigation with up arrow
 * - Input clearing after submission
 * - Disabled state during processing
 * - Blinking cursor when enabled
 * 
 * Requirements: 3.1, 3.4, 3.5
 */

import { useState, useRef, useEffect, KeyboardEvent, ChangeEvent } from 'react';
import { CommandInputProps } from '../types';
import '../styles/CommandInput.css';

/**
 * CommandInput component
 * 
 * Provides a text input field for entering game commands with history navigation
 */
const CommandInput: React.FC<CommandInputProps> = ({ onSubmit, disabled }) => {
  const [inputValue, setInputValue] = useState<string>('');
  const [commandHistory, setCommandHistory] = useState<string[]>([]);
  const [historyIndex, setHistoryIndex] = useState<number>(-1);
  const inputRef = useRef<HTMLInputElement>(null);

  /**
   * Focus input on mount and when disabled state changes
   */
  useEffect(() => {
    if (!disabled && inputRef.current) {
      inputRef.current.focus();
    }
  }, [disabled]);

  /**
   * Handle input change
   */
  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    setInputValue(e.target.value);
    // Reset history index when user types
    setHistoryIndex(-1);
  };

  /**
   * Handle command submission
   * Requirement 3.1: Send command on Enter key
   * Requirement 3.4: Clear input after submission
   */
  const handleSubmit = () => {
    const trimmedCommand = inputValue.trim();
    
    if (trimmedCommand && !disabled) {
      // Add to history (avoid duplicates of the last command)
      if (commandHistory.length === 0 || commandHistory[commandHistory.length - 1] !== trimmedCommand) {
        setCommandHistory(prev => [...prev, trimmedCommand]);
      }
      
      // Submit command
      onSubmit(trimmedCommand);
      
      // Clear input (Requirement 3.4)
      setInputValue('');
      
      // Reset history index
      setHistoryIndex(-1);
    }
  };

  /**
   * Handle keyboard events
   * Requirement 3.1: Submit on Enter key
   * Requirement 3.5: Navigate history with up arrow
   */
  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleSubmit();
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      // Navigate to previous command in history (Requirement 3.5)
      if (commandHistory.length > 0) {
        const newIndex = historyIndex === -1 
          ? commandHistory.length - 1 
          : Math.max(0, historyIndex - 1);
        
        setHistoryIndex(newIndex);
        setInputValue(commandHistory[newIndex]);
      }
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      // Navigate to next command in history
      if (historyIndex !== -1) {
        const newIndex = historyIndex + 1;
        
        if (newIndex >= commandHistory.length) {
          // Back to empty input
          setHistoryIndex(-1);
          setInputValue('');
        } else {
          setHistoryIndex(newIndex);
          setInputValue(commandHistory[newIndex]);
        }
      }
    }
  };

  return (
    <div className="command-input-container">
      <label htmlFor="command-input" className="command-input-label">
        Command:
      </label>
      <input
        id="command-input"
        ref={inputRef}
        type="text"
        className={`command-input ${disabled ? 'command-input--disabled' : ''}`}
        value={inputValue}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        disabled={disabled}
        placeholder={disabled ? 'Processing...' : 'Enter command...'}
        aria-label="Game command input"
        aria-disabled={disabled}
        autoComplete="off"
        spellCheck={false}
      />
    </div>
  );
};

export default CommandInput;
