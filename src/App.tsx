/**
 * Root App component
 * This is a placeholder that will be expanded in subsequent tasks
 */
function App() {
  return (
    <div style={{ 
      padding: '2rem', 
      textAlign: 'center',
      minHeight: '100vh',
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'center',
      alignItems: 'center'
    }}>
      <h1 style={{ 
        fontFamily: 'var(--font-heading)',
        fontSize: 'var(--font-size-2xl)',
        marginBottom: 'var(--spacing-lg)'
      }}>
        West of Haunted House
      </h1>
      <p style={{ 
        fontFamily: 'var(--font-body)',
        fontSize: 'var(--font-size-lg)',
        color: 'var(--color-text-secondary)'
      }}>
        The Grimoire awaits...
      </p>
      <p style={{ 
        fontFamily: 'var(--font-mono)',
        fontSize: 'var(--font-size-sm)',
        color: 'var(--color-text-dim)',
        marginTop: 'var(--spacing-xl)'
      }}>
        Frontend setup complete. Components will be added in subsequent tasks.
      </p>
    </div>
  );
}

export default App;
