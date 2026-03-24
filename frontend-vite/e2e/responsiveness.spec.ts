import { test, expect } from '@playwright/test';

const routes = ['/', '/recommend', '/statistics', '/chat'];

for (const route of routes) {
  test.describe(`Responsiveness: ${route}`, () => {
    test(`no horizontal overflow at any viewport`, async ({ page }) => {
      await page.goto(route);
      await page.waitForLoadState('networkidle');

      // Check that document width equals viewport width (no overflow)
      const hasOverflow = await page.evaluate(() => {
        return document.documentElement.scrollWidth > document.documentElement.clientWidth;
      });
      expect(hasOverflow).toBe(false);
    });
  });
}
