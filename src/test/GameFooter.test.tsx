/**
 * GameFooter Component Tests
 * Feature: grimoire-frontend
 * 
 * Tests for the game instructions footer component
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import GameFooter from '../components/GameFooter';

describe('GameFooter', () => {
  it('renders the footer with all sections', () => {
    render(<GameFooter />);
    
    // Check for section titles
    expect(screen.getByText(/How to Play/i)).toBeInTheDocument();
    expect(screen.getByText(/Common Commands/i)).toBeInTheDocument();
    expect(screen.getByText(/Directions/i)).toBeInTheDocument();
  });

  it('displays common game commands', () => {
    render(<GameFooter />);
    
    // Check for essential commands
    expect(screen.getByText('LOOK')).toBeInTheDocument();
    expect(screen.getByText('TAKE [object]')).toBeInTheDocument();
    expect(screen.getByText('EXAMINE [object]')).toBeInTheDocument();
    expect(screen.getByText('INVENTORY')).toBeInTheDocument();
    expect(screen.getByText('USE [object]')).toBeInTheDocument();
  });

  it('displays directional commands', () => {
    render(<GameFooter />);
    
    // Check for all directions
    expect(screen.getByText('NORTH')).toBeInTheDocument();
    expect(screen.getByText('SOUTH')).toBeInTheDocument();
    expect(screen.getByText('EAST')).toBeInTheDocument();
    expect(screen.getByText('WEST')).toBeInTheDocument();
    expect(screen.getByText('UP')).toBeInTheDocument();
    expect(screen.getByText('DOWN')).toBeInTheDocument();
  });

  it('displays the sanity warning', () => {
    render(<GameFooter />);
    
    expect(screen.getByText(/sanity may waver/i)).toBeInTheDocument();
  });

  it('has proper semantic HTML structure', () => {
    const { container } = render(<GameFooter />);
    
    // Should use footer element
    const footer = container.querySelector('footer');
    expect(footer).toBeInTheDocument();
    expect(footer).toHaveClass('game-footer');
  });
});
