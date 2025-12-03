/**
 * Test setup file for vitest
 * Feature: grimoire-frontend
 */

import '@testing-library/jest-dom';

// Mock environment variables for tests
process.env.VITE_API_BASE_URL = 'http://localhost:3001';
process.env.VITE_API_TIMEOUT = '30000';

// Mock localStorage for tests
class LocalStorageMock {
  private store: Record<string, string> = {};

  clear() {
    this.store = {};
  }

  getItem(key: string) {
    return this.store[key] || null;
  }

  setItem(key: string, value: string) {
    this.store[key] = String(value);
  }

  removeItem(key: string) {
    delete this.store[key];
  }

  get length() {
    return Object.keys(this.store).length;
  }

  key(index: number) {
    const keys = Object.keys(this.store);
    return keys[index] || null;
  }
}

global.localStorage = new LocalStorageMock() as Storage;

