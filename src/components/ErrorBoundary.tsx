/**
 * ErrorBoundary Component
 * Feature: grimoire-frontend
 * 
 * React error boundary to catch and handle errors in the component tree.
 * Provides a fallback UI when errors occur and prevents the entire app from crashing.
 * 
 * Requirements: 5.1 (error handling for session initialization)
 */

import { Component, ErrorInfo, ReactNode } from 'react';

/**
 * Props for ErrorBoundary component
 */
interface ErrorBoundaryProps {
  children: ReactNode;
}

/**
 * State for ErrorBoundary component
 */
interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

/**
 * ErrorBoundary component
 * 
 * Catches JavaScript errors anywhere in the child component tree,
 * logs those errors, and displays a fallback UI instead of crashing.
 */
class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  /**
   * Update state when an error is caught
   */
  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return {
      hasError: true,
      error,
    };
  }

  /**
   * Log error details
   */
  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    console.error('ErrorBoundary caught an error:', error);
    console.error('Error info:', errorInfo);
    
    this.setState({
      error,
      errorInfo,
    });
  }

  /**
   * Reset error state and reload the page
   */
  handleReset = (): void => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
    
    // Reload the page to start fresh
    window.location.reload();
  };

  render(): ReactNode {
    if (this.state.hasError) {
      return (
        <div className="error-boundary">
          <div className="error-boundary__content">
            <h1 className="error-boundary__title">Something went wrong</h1>
            
            <p className="error-boundary__message">
              The grimoire has encountered an unexpected error. 
              Please try refreshing the page to start a new game.
            </p>
            
            {this.state.error && (
              <details className="error-boundary__details">
                <summary>Error details</summary>
                <pre className="error-boundary__stack">
                  {this.state.error.toString()}
                  {this.state.errorInfo && this.state.errorInfo.componentStack}
                </pre>
              </details>
            )}
            
            <button
              className="error-boundary__button"
              onClick={this.handleReset}
              type="button"
            >
              Reload Page
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
