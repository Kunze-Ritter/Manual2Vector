// Playwright E2E tests for authentication flows
import { test, expect } from '@playwright/test';
import { LoginPage } from './page-objects/LoginPage';
import { DashboardPage } from './page-objects/DashboardPage';

const loginAsAdmin = async (page: any) => {
  const loginPage = new LoginPage(page);
  await loginPage.navigate();
  await loginPage.login('admin@test.com', 'test123456');
};

const loginAsEditor = async (page: any) => {
  const loginPage = new LoginPage(page);
  await loginPage.navigate();
  await loginPage.login('editor@test.com', 'test123456');
};

const loginAsViewer = async (page: any) => {
  const loginPage = new LoginPage(page);
  await loginPage.navigate();
  await loginPage.login('viewer@test.com', 'test123456');
};

const logout = async (page: any) => {
  const dashboardPage = new DashboardPage(page);
  await dashboardPage.logout();
};

test.describe('Authentication', () => {
  test('Admin can login and see dashboard', async ({ page }) => {
    await loginAsAdmin(page);
    const dashboardPage = new DashboardPage(page);
    await expect(page.locator('[data-testid="dashboard"]')).toBeVisible();
    const userRole = await dashboardPage.getUserRole();
    await expect(page.locator('[data-testid="user-role"]').first()).toHaveText('admin');
    await logout(page);
  });

  test('Editor login', async ({ page }) => {
    await loginAsEditor(page);
    const dashboardPage = new DashboardPage(page);
    await expect(page.locator('[data-testid="dashboard"]')).toBeVisible();
    await expect(page.locator('[data-testid="user-role"]').first()).toHaveText('editor');
    await logout(page);
  });

  test('Viewer login', async ({ page }) => {
    await loginAsViewer(page);
    const dashboardPage = new DashboardPage(page);
    await expect(page.locator('[data-testid="dashboard"]')).toBeVisible();
    await expect(page.locator('[data-testid="user-role"]').first()).toHaveText('viewer');
    await logout(page);
  });
});
