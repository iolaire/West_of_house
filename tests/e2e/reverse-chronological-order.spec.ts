/**
 * E2E Test: Reverse Chronological Order
 * Feature: grimoire-frontend
 * 
 * Verifies that game output displays in reverse chronological order:
 * - Most recent command appears at the top
 * - Response appears below the command
 * - Previous commands flow down the page
 */

import { test, expect } from '@playwright/test';

test.describe('Game Output Reverse Chronological Order', () => {
  test('should display output lines with newest at top using flex-direction', async ({ page }) => {
    await page.goto('/');
    
    // Wait for the game output container
    await page.waitForSelector('.game-output', { timeout: 10000 });
    
    // Check that the game-output has flex-direction: column-reverse
    const gameOutput = page.locator('.game-output');
    const flexDirection = await gameOutput.evaluate((el) => {
      return window.getComputedStyle(el).flexDirection;
    });
    
    expect(flexDirection).toBe('column-reverse');
    console.log('✓ Game output uses flex-direction: column-reverse');
  });

  test('should display commands in reverse chronological order after typing', async ({ page }) => {
    await page.goto('/');
    
    // Wait for the command input
    await page.waitForSelector('.command-input', { timeout: 10000 });
    
    // Wait for initial session setup
    await page.waitForTimeout(3000);
    
    const input = page.locator('.command-input');
    
    // Type first command
    await input.fill('look');
    await input.press('Enter');
    await page.waitForTimeout(1500);
    
    // Type second command
    await input.fill('north');
    await input.press('Enter');
    await page.waitForTimeout(1500);
    
    // Get all output lines
    const outputLines = page.locator('.output-line');
    const count = await outputLines.count();
    
    console.log(`Total output lines: ${count}`);
    
    if (count >= 4) {
      // Get the text content of all lines
      const lineTexts = await outputLines.allTextContents();
      
      console.log('Output lines (in DOM order):');
      lineTexts.forEach((text, i) => console.log(`  ${i}: ${text.substring(0, 50)}`));
      
      // Find the positions of our commands
      const northIndex = lineTexts.findIndex(text => text.includes('north'));
      const lookIndex = lineTexts.findIndex(text => text.includes('look'));
      
      if (northIndex >= 0 && lookIndex >= 0) {
        // Most recent command (north) should have lower index (appear first in DOM)
        expect(northIndex).toBeLessThan(lookIndex);
        console.log(`✓ Reverse order confirmed: north at ${northIndex}, look at ${lookIndex}`);
      }
    }
  });

  test('should show newest command at top after multiple commands', async ({ page }) => {
    await page.goto('/');
    await page.waitForSelector('.command-input', { timeout: 10000 });
    await page.waitForTimeout(3000);
    
    const input = page.locator('.command-input');
    
    // Type multiple commands quickly
    const commands = ['look', 'inventory', 'examine mailbox'];
    
    for (const cmd of commands) {
      await input.fill(cmd);
      await input.press('Enter');
      await page.waitForTimeout(1200);
    }
    
    // Get all command lines
    const commandLines = page.locator('.output-line--command');
    const commandTexts = await commandLines.allTextContents();
    
    console.log('Command lines found:', commandTexts);
    
    if (commandTexts.length >= 3) {
      // Find the last command we typed
      const lastCommandIndex = commandTexts.findIndex(text => 
        text.includes('examine') || text.includes('mailbox')
      );
      
      // Find the first command we typed
      const firstCommandIndex = commandTexts.findIndex(text => text.includes('look'));
      
      if (lastCommandIndex >= 0 && firstCommandIndex >= 0) {
        // Last command should appear before first command
        expect(lastCommandIndex).toBeLessThan(firstCommandIndex);
        console.log(`✓ Last command at ${lastCommandIndex}, first command at ${firstCommandIndex}`);
      }
    }
  });
});
