import { test, expect } from '@playwright/test';

test.skip('Verify LUTAR button visibility when selecting two paddles', async ({ page }) => {
  await page.goto('http://localhost:3001');
  
  await page.waitForSelector('button:has-text("COMPARAR"), button:has-text("SELECIONADA")');

  const compareButtons = page.locator('button:has-text("COMPARAR"), button:has-text("SELECIONADA")');
  
  await compareButtons.nth(0).click({ force: true });
  await page.waitForTimeout(300);

  await expect(page.locator('text=raquetes selecionadas')).toBeVisible();

  const lutarButton = page.locator('button:has-text("LUTAR!")');
  await expect(lutarButton).toBeVisible();
  await expect(lutarButton).toBeDisabled();

  await compareButtons.nth(1).click({ force: true });
  await page.waitForTimeout(300);

  await expect(lutarButton).toBeEnabled();
});
