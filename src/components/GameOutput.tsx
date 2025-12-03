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

  // Trim lines to MAX_OUTPUT_LINES if needed
  const trimmedLines = lines.length > MAX_OUTPUT_LINES 
    ? lines.slice(lines.length - MAX_OUTPUT_LINES)
    : lines;

  // Handle auto-scroll behavior
  useEffect(() => {
    if (!outputRef.current) return;

    const element = outputRef.current;
    
    // Check if user has scrolled up manually
    const isScrolledToBottom = 
      element.scrollHeight - element.scrollTop <= element.clientHeight + 50;

    // Update autoScroll state based on user scroll position
    if (!isScrolledToBottom && autoScroll) {
      setAutoScroll(false);
    }

    // Auto-scroll to bottom when new content is added and autoScroll is enabled
    if (lines.length > prevLinesLengthRef.current && autoScroll) {
      element.scrollTop = element.scrollHeight;
    }

    // Update previous lines length
    prevLinesLengthRef.current = lines.length;
  }, [lines, autoScroll]);

  // Handle scroll event to detect when user scrolls to bottom
  const handleScroll = () => {
    if (!outputRef.current) return;

    const element = outputRef.current;
    const isScrolledToBottom = 
      element.scrollHeight - element.scrollTop <= element.clientHeight + 50;

    // Re-enable auto-scroll when user scrolls back to bottom
    if (isScrolledToBottom && !autoScroll) {
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
    >
      {trimmedLines.map((line) => (
        <OutputLineComponent key={line.id} line={line} />
      ))}
    </div>
  );
};

/**
 * OutputLineComponent renders a single output line
 */
const OutputLineComponent: React.FC<{ line: OutputLine }> = ({ line }) => {
  const className = `output-line output-line--${line.type}`;
  
  return (
    <div className={className} data-timestamp={line.timestamp}>
      {line.type === 'command' && <span className="output-line__prompt">&gt; </span>}
      <span className="output-line__text">{line.text}</span>
    </div>
  );
};

export default GameOutput;
