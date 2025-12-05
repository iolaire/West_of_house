/**
 * AboutModal Component
 * Feature: grimoire-frontend
 *
 * Full-screen modal overlay for About information
 * Fills the entire viewport with dark overlay
 * Includes close button and scrollable content area
 */

import React, { useEffect, useRef } from 'react';
import { AboutModalProps } from '../types';
import '../styles/AboutModal.css';

/**
 * AboutModal component
 *
 * Displays about information in a full-screen overlay
 * Handles escape key to close and click outside to close
 */
const AboutModal: React.FC<AboutModalProps> = ({ onClose }) => {
  const modalRef = useRef<HTMLDivElement>(null);

  // Handle escape key press
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => {
      document.removeEventListener('keydown', handleEscape);
    };
  }, [onClose]);

  // Focus trap for accessibility
  useEffect(() => {
    if (modalRef.current) {
      modalRef.current.focus();
    }
  }, []);

  // Handle click outside modal content
  const handleBackdropClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div
      className="about-modal-backdrop"
      onClick={handleBackdropClick}
      role="dialog"
      aria-modal="true"
      aria-labelledby="about-title"
      ref={modalRef}
      tabIndex={-1}
    >
      <div className="about-modal-content">
        <div className="about-modal-header">
          <h2 id="about-title" className="about-modal-title">About West of Haunted House</h2>
          <button
            className="about-modal-close"
            onClick={onClose}
            aria-label="Close About dialog"
            title="Close (Esc)"
          >
            <span aria-hidden="true">×</span>
          </button>
        </div>

        <div className="about-modal-body">
          <div className="about-content">
            <h3>Welcome to West of Haunted House</h3>
            <p>
              West of Haunted House is a text-based adventure game that draws inspiration
              from the classic Zork series. Step into a mysterious world filled with
              dark secrets, haunted locations, and puzzles waiting to be solved.
            </p>

            <h3>How to Play</h3>
            <p>
              Type commands into the grimoire to explore the haunted realm. The game
              responds to your words with descriptions of your surroundings and the
              consequences of your actions.
            </p>

            <h3>Features</h3>
            <ul>
              <li>Immersive text-based gameplay with rich descriptions</li>
              <li>Haunted atmospheric setting with spooky undertones</li>
              <li>Classic adventure game mechanics</li>
              <li>Interactive grimoire interface</li>
              <li>Beautiful room imagery to enhance your experience</li>
            </ul>

            <h3>Controls</h3>
            <p>
              Use simple text commands to interact with the world:
            </p>
            <ul>
              <li><strong>MOVEMENT:</strong> GO [direction] - Move north, south, east, west, up, or down</li>
              <li><strong>INTERACTION:</strong> TAKE [object], EXAMINE [object], USE [object]</li>
              <li><strong>INFORMATION:</strong> LOOK - Examine your current location</li>
              <li><strong>INVENTORY:</strong> INVENTORY - Check what you're carrying</li>
              <li><strong>HISTORY:</strong> Use UP/DOWN arrows to navigate command history</li>
            </ul>

            <h3>Tips</h3>
            <p>
              • Read carefully - descriptions often contain important clues<br/>
              • Try examining objects multiple times<br/>
              • Not all paths are obvious - think creatively<br/>
              • Save often if the game supports it<br/>
              • Some areas may require specific items to access
            </p>

            <h3>The Creator</h3>
            <p>
              • Iolaire McFadden created this<br/>
              • To provide feedback visit the <a href="https://www.geeksforgeeks.org/">West of House</a> project on github and submit an issue.

            </p>

            <p className="about-footer-text">
              <em>Enter if you dare... The spirits await your arrival.</em>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AboutModal;