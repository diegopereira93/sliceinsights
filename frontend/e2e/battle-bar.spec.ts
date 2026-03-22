import { test, expect } from '@playwright/test';

test('Verify LUTAR button visibility when selecting two paddles', async ({ page }) => {
  // Go to the local dev server
  await page.goto('http://localhost:3002');
  
  // Wait for paddles to load (look for COMPARAR buttons)
  await page.waitForSelector('button:has-text("COMPARAR")');

  const compareButtons = page.locator('button:has-text("COMPARAR")');
  
  // Click the first one
  await compareButtons.nth(0).click();

  // The battle bar should appear with 1 racket
  await expect(page.locator('text=1 raquete selecionada')).toBeVisible();

  // The LUTAR button should be visible but disabled
  const lutarButton = page.locator('button:has-text("LUTAR!")');
  await expect(lutarButton).toBeVisible();
  await expect(lutarButton).toBeDisabled();

  // Click the second one
  await compareButtons.nth(1).click();

  // The battle bar should update to 2 rackets
  await expect(page.locator('text=2 raquetes selecionadas')).toBeVisible();

  // The LUTAR button should still be visible and NOW enabled
  await expect(lutarButton).toBeVisible();
  await expect(lutarButton).toBeEnabled();
});
