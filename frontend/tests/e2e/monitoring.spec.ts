// Playwright E2E tests for monitoring WebSocket and alert flows
import { test, expect } from '@playwright/test';
// import type { Page } from '@playwright/test'; // removed unused import
import { loginAsAdmin } from './fixtures/auth.fixture';

test.describe('Monitoring', () => {
  test('WebSocket connects, reconnects with exponential backoff after forced close, and receives pipeline updates', async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto('/monitoring');
    const pipelineStatus = page.locator('[data-testid="pipeline-status"]');
    await expect(pipelineStatus).toBeVisible();
    // Force close the WebSocket
    await page.evaluate(() => {
      // @ts-ignore
      if ((window as any).testWebSocket) {
        // @ts-ignore
        (window as any).testWebSocket.close(4000, 'test forced close');
      }
    });
    // Poll for reconnect attempts and delay values
    await expect.poll(async () => {
      return await page.evaluate(() => (window as any).__wsReconnectAttempts || 0);
    }).toBeGreaterThanOrEqual(1);
    const firstDelay = await page.evaluate(() => (window as any).__wsReconnectDelayMs);
    // Wait for second attempt
    await page.waitForTimeout(firstDelay + 500);
    await expect.poll(async () => {
      return await page.evaluate(() => (window as any).__wsReconnectAttempts || 0);
    }).toBeGreaterThanOrEqual(2);
    const secondDelay = await page.evaluate(() => (window as any).__wsReconnectDelayMs);
    // Verify exponential backoff (approx double)
    expect(secondDelay).toBeGreaterThanOrEqual(firstDelay * 1.8);
    // Ensure UI shows connected again
    await page.waitForFunction(() => {
      const status = document.querySelector('[data-testid="pipeline-status"]');
      return status && status.textContent?.includes('connected');
    }, { timeout: 15000 });
    await expect(pipelineStatus).toBeVisible();
  });

  test('Alert appears and can be acknowledged', async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto('/monitoring');
    const alert = page.locator('[data-testid="alert-item"]').first();
    await expect(alert).toBeVisible();
    await alert.locator('[data-testid="acknowledge-button"]').click();
    await expect(alert).toBeHidden();
  });

  test('Alert can be dismissed via DELETE request', async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto('/monitoring');
    const alert = page.locator('[data-testid="alert-item"]').first();
    await expect(alert).toBeVisible();
    // Intercept DELETE request
    const [response] = await Promise.all([
      page.waitForResponse((r: any) => r.url().match(/\/api\/v1\/monitoring\/alerts\/\d+$/) && r.request().method() === 'DELETE'),
      alert.locator('[data-testid="dismiss-button"]').click(),
    ]);
    expect(response.ok()).toBeTruthy();
    await expect(alert).toBeHidden();
  });
});
