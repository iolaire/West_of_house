import React from 'react';
import ReactDOM from 'react-dom/client';
import { Amplify } from 'aws-amplify';
import outputs from '../amplify_outputs.json';
import App from './App';
import './styles/global.css';

// Configure Amplify with backend outputs
// This must happen before any Amplify services are used
Amplify.configure(outputs, {
  ssr: false // Disable SSR mode to prevent Safari timing warnings
});

const rootElement = document.getElementById('root');

if (!rootElement) {
  throw new Error('Root element not found');
}

ReactDOM.createRoot(rootElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
