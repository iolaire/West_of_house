/**
 * E2E Test: Mailbox and Parchment Interaction
 * Feature: complete-zork-commands
 * 
 * Verifies the complete workflow:
 * 1. Open the mailbox
 * 2. Take the parchment (leaflet object)
 * 3. Read the parchment
 */

import { test, expect } from '@playwright/test';

test.describe('Mailbox and Parchment Workflow', () => {
  test('should open mailbox, take parchment, and read it', async ({ page }) => {
    await page.goto('/');
    
    // Wait for the game to load
    await page.waitForSelector('.command-input', { timeout: 10000 });
    await page.waitForTimeout(3000);
    
    const input = page.locator('.command-input');
    
    // Step 1: Open the mailbox
    console.log('Step 1: Opening mailbox...');
    await input.fill('open mailbox');
    await input.press('Enter');
    await page.waitForTimeout(2000);
    
    // Verify mailbox opened
    const outputLines = page.locator('.output-line');
    const allText = await outputLines.allTextContents();
    const openResponse = allText.find(text => 
      text.toLowerCase().includes('mailbox') && 
      (text.toLowerCase().includes('open') || text.toLowerCase().includes('parchment'))
    );
    
    expect(openResponse).toBeTruthy();
    console.log('✓ Mailbox opened:', openResponse?.substring(0, 80));
    
    // Step 2: Take the parchment
    console.log('Step 2: Taking parchment...');
    await input.fill('take parchment');
    await input.press('Enter');
    await page.waitForTimeout(2000);
    
    // Verify parchment was taken
    const allText2 = await outputLines.allTextContents();
    const takeResponse = allText2.find(text => 
      text.toLowerCase().includes('parchment') || 
      text.toLowerCase().includes('taken') ||
      text.toLowerCase().includes('grasp')
    );
    
    expect(takeResponse).toBeTruthy();
    console.log('✓ Parchment taken:', takeResponse?.substring(0, 80));
    
    // Step 3: Read the parchment
    console.log('Step 3: Reading parchment...');
    await input.fill('read parchment');
    await input.press('Enter');
    await page.waitForTimeout(2000);
    
    // Verify parchment was read
    const allText3 = await outputLines.allTextContents();
    const readResponse = allText3.find(text => 
      text.toLowerCase().includes('abandon hope') || 
      text.toLowerCase().includes('haunted manor') ||
      text.toLowerCase().includes('nightmare')
    );
    
    expect(readResponse).toBeTruthy();
    console.log('✓ Parchment read:', readResponse?.substring(0, 80));
  });

  test('should also work with "leaflet" as object name', async ({ page }) => {
    await page.goto('/');
    await page.waitForSelector('.command-input', { timeout: 10000 });
    await page.waitForTimeout(3000);
    
    const input = page.locator('.command-input');
    
    // Open mailbox
    await input.fill('open mailbox');
    await input.press('Enter');
    await page.waitForTimeout(2000);
    
    // Try taking with "leaflet" (the actual object ID)
    await input.fill('take leaflet');
    await input.press('Enter');
    await page.waitForTimeout(2000);
    
    const outputLines = page.locator('.output-line');
    const allText = await outputLines.allTextContents();
    const takeResponse = allText.find(text => 
      text.toLowerCase().includes('taken') ||
      text.toLowerCase().includes('grasp') ||
      text.toLowerCase().includes('parchment')
    );
    
    expect(takeResponse).toBeTruthy();
    console.log('✓ Leaflet taken:', takeResponse?.substring(0, 80));
  });
});
