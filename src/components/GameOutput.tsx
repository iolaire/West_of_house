/**
 * GameOutput Component
 * Feature: grimoire-frontend
 * 
 * Displays scrollable command history and game responses with auto-scroll behavior
 * and a 1000-line limit for performance.
 */

import { useEffect, useRef, useState } from 'react';
import { GameOutputProps, OutputLine, MAX_OUTPUT_LINES } from '../types';
import '../styles/GameOutput.css';

/**
 * GameOutput component renders the scrollable output area for command history
 * 
 * Features:
 * - Displays commands, responses, and errors
 * - Auto-scrolls to bottom on new content
 * - Allows manual scrolling to review history
 * - Trims oldest entries when exceeding 1000 lines
 */
const GameOutput: React.FC<GameOutputProps> = ({ lines }) => {
  const outputRef = useRef<HTMLDivElement>(null);
  const [autoScroll, setAutoScroll] = useState(true);
  const prevLinesLengthRef = useRef(lines.length);

  // Trim lines to MAX_OUTPUT_LINES if needed, then reverse for newest-first display
  const trimmedLines = lines.length > MAX_OUTPUT_LINES 
    ? lines.slice(lines.length - MAX_OUTPUT_LINES)
    : lines;
  
  // Reverse the array so newest entries appear at top
  const reversedLines = [...trimmedLines].reverse();

  // Handle auto-scroll behavior (scroll to top for newest content)
  useEffect(() => {
    if (!outputRef.current) return;

    const element = outputRef.current;
    
    // Check if user has scrolled down manually
    const isScrolledToTop = element.scrollTop <= 50;

    // Update autoScroll state based on user scroll position
    if (!isScrolledToTop && autoScroll) {
      setAutoScroll(false);
    }

    // Auto-scroll to top when new content is added and autoScroll is enabled
    if (lines.length > prevLinesLengthRef.current && autoScroll) {
      element.scrollTop = 0;
    }

    // Update previous lines length
    prevLinesLengthRef.current = lines.length;
  }, [lines, autoScroll]);

  // Handle scroll event to detect when user scrolls to top
  const handleScroll = () => {
    if (!outputRef.current) return;

    const element = outputRef.current;
    const isScrolledToTop = element.scrollTop <= 50;

    // Re-enable auto-scroll when user scrolls back to top
    if (isScrolledToTop && !autoScroll) {
      setAutoScroll(true);
    }
  };

  return (
    <div 
      className="game-output" 
      ref={outputRef}
      onScroll={handleScroll}
      role="log"
      aria-live="polite"
      aria-atomic="false"
      aria-label="Game output history"
      tabIndex={0}
    >
      {reversedLines.length === 0 ? (
        <div className="output-line output-line--empty" aria-label="No game output yet">
          <span className="output-line__text">The grimoire awaits your command...</span>
        </div>
      ) : (
        reversedLines.map((line) => (
          <OutputLineComponent key={line.id} line={line} />
        ))
      )}
    </div>
  );
};

/**
 * OutputLineComponent renders a single output line
 */
const OutputLineComponent: React.FC<{ line: OutputLine }> = ({ line }) => {
  const className = `output-line output-line--${line.type}`;
  
  // Determine appropriate ARIA role and label based on line type
  const ariaRole = line.type === 'error' ? 'alert' : undefined;
  const ariaLabel = line.type === 'command' 
    ? `Command: ${line.text}` 
    : line.type === 'error'
    ? `Error: ${line.text}`
    : `Response: ${line.text}`;
  
  return (
    <div 
      className={className} 
      data-timestamp={line.timestamp}
      role={ariaRole}
      aria-label={ariaLabel}
    >
      {line.type === 'command' && <span className="output-line__prompt" aria-hidden="true">&gt; </span>}
      <span className="output-line__text">{line.text}</span>
    </div>
  );
};

export default GameOutput;
