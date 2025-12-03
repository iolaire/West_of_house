/**
 * Test setup file for vitest
 * Feature: grimoire-frontend
 */

import '@testing-library/jest-dom';

// Mock environment variables for tests
process.env.VITE_API_BASE_URL = 'http://localhost:3001';
process.env.VITE_API_TIMEOUT = '30000';

