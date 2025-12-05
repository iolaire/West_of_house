/**
 * Root App component
 * Feature: grimoire-frontend
 * 
 * Provides session context and renders the main grimoire interface.
 * Wraps the application in an ErrorBoundary to catch and handle errors gracefully.
 * 
 * Requirements: 5.1 (session management and initialization)
 */

import { SessionProvider } from './contexts/SessionContext';
import PageHeader from './components/PageHeader';
import GrimoireContainer from './components/GrimoireContainer';
import ErrorBoundary from './components/ErrorBoundary';
import './styles/ErrorBoundary.css';

/**
 * App component
 * 
 * Root component that:
 * - Wraps application in ErrorBoundary for error handling
 * - Provides SessionManager context to all child components
 * - Renders the main GrimoireContainer
 * - Includes skip link for keyboard navigation accessibility
 * 
 * Session initialization happens in GrimoireContainer on mount (Requirement 5.1)
 */
function App() {
  return (
    <ErrorBoundary>
      <a href="#main-content" className="skip-link">
        Skip to main content
      </a>
      <SessionProvider>
        <GrimoireContainer />
      </SessionProvider>
    </ErrorBoundary>
  );
}

export default App;
