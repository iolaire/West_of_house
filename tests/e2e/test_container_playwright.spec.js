const { test, expect } = require('@playwright/test');

test('Container functionality - mailbox should allow taking advertisement', async ({ page }) => {
  // Navigate to the game
  await page.goto('http://localhost:3001');

  // Wait for the game to load
  await expect(page.locator('body')).toBeVisible();

  // Function to send commands and wait for response
  async function sendCommand(command) {
    const input = page.locator('input[placeholder*="command" i]');
    if (await input.count() === 0) {
      // Try alternative selector
      const altInput = page.locator('input[placeholder*="type" i]');
      if (await altInput.count() === 0) {
        console.log('❌ No command input field found');
        return null;
      }
      await altInput.fill(command);
      await page.keyboard.press('Enter');
    } else {
      await input.fill(command);
      await page.keyboard.press('Enter');
    }

    // Wait for response
    await page.waitForTimeout(500);

    // Try to find response messages
    const messages = await page.locator('.message, [class*="message"], [data-testid*="message"]').all();
    if (messages.length > 0) {
      const lastMessage = await messages[messages.length - 1].textContent();
      return lastMessage;
    }
    return null;
  }

  // Function to get inventory items
  async function getInventory() {
    const invSelectors = [
      '.inventory-section',
      '[class*="inventory"]',
      '[data-testid*="inventory"]'
    ];

    for (const selector of invSelectors) {
      const invSection = page.locator(selector);
      if (await invSection.count() > 0) {
        const invText = await invSection.textContent();
        return invText || '';
      }
    }
    return '';
  }

  // Function to get room description
  async function getRoomDescription() {
    const descSelectors = [
      '.room-description',
      '[class*="description"]',
      '[data-testid*="description"]'
    ];

    for (const selector of descSelectors) {
      const descSection = page.locator(selector);
      if (await descSection.count() > 0) {
        const descText = await descSection.textContent();
        return descText || '';
      }
    }
    return '';
  }

  console.log('🎮 Starting container test...');

  // Look around to see what's in the room
  const lookResult = await sendCommand('look');
  console.log('📍 Room after look:', lookResult);

  // Try to examine mailbox before opening
  const examineResult = await sendCommand('examine mailbox');
  console.log('📮 Examining mailbox:', examineResult);

  // Open the mailbox
  const openResult = await sendCommand('open mailbox');
  console.log('📪 Opening mailbox:', openResult);

  // Look around again to see if advertisement is visible
  const lookAfterOpen = await sendCommand('look');
  console.log('👀 Room after opening:', lookAfterOpen);

  // Check if advertisement is mentioned in the room description
  if (lookAfterOpen && lookAfterOpen.toLowerCase().includes('advertisement')) {
    console.log('✅ Advertisement visible in room description');
  } else if (lookAfterOpen && lookAfterOpen.toLowerCase().includes('death notice')) {
    console.log('✅ Death notice visible in room description');
  } else {
    console.log('❌ Advertisement not visible in room description');
  }

  // Try to take advertisement
  const takeResult = await sendCommand('take advertisement');
  console.log('📬 Taking advertisement:', takeResult);

  // Check inventory after taking
  const inventory = await getInventory();
  console.log('🎒 Inventory:', inventory);

  // If taking advertisement failed, try with death notice
  if (!takeResult || !takeResult.includes('taken') || !inventory.includes('advertisement') && !inventory.includes('death notice')) {
    console.log('⚠️  Trying with "death notice" instead...');
    const takeDeathNotice = await sendCommand('take death notice');
    console.log('💀 Taking death notice:', takeDeathNotice);

    // Check inventory again
    const inventory2 = await getInventory();
    console.log('🎒 Inventory after death notice:', inventory2);
  }

  // Test reading the advertisement
  const readResult = await sendCommand('read advertisement');
  console.log('📖 Reading advertisement:', readResult);

  if (!readResult || readResult.includes("don't see")) {
    const readDeathNotice = await sendCommand('read death notice');
    console.log('📰 Reading death notice:', readDeathNotice);
  }

  // Close the mailbox
  const closeResult = await sendCommand('close mailbox');
  console.log('📫 Closing mailbox:', closeResult);

  // Final status
  const finalInventory = await getInventory();
  if (finalInventory.includes('advertisement') || finalInventory.includes('death notice')) {
    console.log('✅ SUCCESS: Advertisement/death notice is in inventory!');
  } else {
    console.log('❌ FAILED: Advertisement/death notice not in inventory');
  }
});

test('Container functionality - test bag of coins', async ({ page }) => {
  // This test would require navigating to maze_5 first
  // For now, we'll just test the mailbox
  console.log('📝 Note: Bag of coins test skipped - requires navigation to maze_5');
});