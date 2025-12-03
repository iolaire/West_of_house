/**
 * Root App component
 * Feature: grimoire-frontend
 * 
 * Provides session context and renders the main grimoire interface
 * Requirements: 5.1 (session management)
 */

import { SessionProvider } from './contexts/SessionContext';
import GrimoireContainer from './components/GrimoireContainer';

function App() {
  return (
    <SessionProvider>
      <GrimoireContainer />
    </SessionProvider>
  );
}

export default App;
