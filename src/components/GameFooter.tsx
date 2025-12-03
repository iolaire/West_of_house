/**
 * GameFooter Component
 * Feature: grimoire-frontend
 * 
 * Displays spooky game instructions and basic commands at the bottom of the grimoire.
 * Provides new players with essential information about how to interact with the game.
 */

import React from 'react';
import '../styles/GameFooter.css';

/**
 * GameFooter component
 * 
 * Shows atmospheric instructions and common commands
 * Styled to match the grimoire aesthetic
 */
const GameFooter: React.FC = () => {
  return (
    <footer 
      className="game-footer"
      role="contentinfo"
      aria-label="Game instructions and commands"
    >
      <div className="footer-content">
        <section className="footer-section" aria-labelledby="how-to-play">
          <h3 id="how-to-play" className="footer-title">
            <span aria-hidden="true">⚰️</span> How to Play
          </h3>
          <p className="footer-text">
            Type commands to explore the haunted realm. The grimoire responds to your words...
          </p>
        </section>
        
        <section className="footer-section" aria-labelledby="common-commands">
          <h3 id="common-commands" className="footer-title">
            <span aria-hidden="true">🕯️</span> Common Commands
          </h3>
          <div className="command-list" role="list">
            <span className="command-item" role="listitem">LOOK</span>
            <span className="command-item" role="listitem">GO [direction]</span>
            <span className="command-item" role="listitem">TAKE [object]</span>
            <span className="command-item" role="listitem">EXAMINE [object]</span>
            <span className="command-item" role="listitem">INVENTORY</span>
            <span className="command-item" role="listitem">USE [object]</span>
          </div>
        </section>
        
        <section className="footer-section" aria-labelledby="directions">
          <h3 id="directions" className="footer-title">
            <span aria-hidden="true">🌙</span> Directions
          </h3>
          <div className="command-list" role="list">
            <span className="command-item" role="listitem">NORTH</span>
            <span className="command-item" role="listitem">SOUTH</span>
            <span className="command-item" role="listitem">EAST</span>
            <span className="command-item" role="listitem">WEST</span>
            <span className="command-item" role="listitem">UP</span>
            <span className="command-item" role="listitem">DOWN</span>
          </div>
        </section>
      </div>
      
      <div className="footer-warning" role="note" aria-label="Warning message">
        <p><span aria-hidden="true">⚠️</span> Beware: Your sanity may waver as you delve deeper into the darkness...</p>
      </div>
    </footer>
  );
};

export default GameFooter;
