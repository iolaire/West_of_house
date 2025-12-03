/**
 * LoadingIndicator Component
 * Feature: grimoire-frontend
 * 
 * Visual feedback during command processing with:
 * - Pulsing animation
 * - Show/hide based on isVisible prop
 * - Positioned near command input
 * - Accessible to screen readers
 * 
 * Requirements: 3.3, 7.1
 */

import React from 'react';
import { LoadingIndicatorProps } from '../types';
import '../styles/LoadingIndicator.css';

/**
 * LoadingIndicator component
 * 
 * Displays a pulsing indicator when commands are being processed
 * Requirement 3.3: Show loading indicator during command processing
 * Requirement 7.1: Provide helpful UI feedback
 */
const LoadingIndicator: React.FC<LoadingIndicatorProps> = ({ isVisible }) => {
  if (!isVisible) {
    return null;
  }

  return (
    <div 
      className="loading-indicator"
      role="status"
      aria-live="polite"
      aria-busy="true"
      aria-label="Processing command"
    >
      <div className="loading-indicator__spinner" aria-hidden="true">
        <div className="loading-indicator__dot loading-indicator__dot--1"></div>
        <div className="loading-indicator__dot loading-indicator__dot--2"></div>
        <div className="loading-indicator__dot loading-indicator__dot--3"></div>
      </div>
      <span className="loading-indicator__text" aria-hidden="true">Processing...</span>
      <span className="visually-hidden">Command is being processed, please wait</span>
    </div>
  );
};

export default LoadingIndicator;
