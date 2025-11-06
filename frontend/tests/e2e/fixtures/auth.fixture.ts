// Auth fixture helpers for Playwright E2E tests
import { Page, APIRequestContext } from '@playwright/test';
import { LoginPage, DashboardPage } from '../page-objects';

const ADMIN_USERNAME = process.env.ADMIN_USERNAME || 'admin@example.com';
const ADMIN_PASSWORD = process.env.ADMIN_PASSWORD || 'adminpass';
const EDITOR_USERNAME = process.env.EDITOR_USERNAME || 'editor@example.com';
const EDITOR_PASSWORD = process.env.EDITOR_PASSWORD || 'editorpass';
const VIEWER_USERNAME = process.env.VIEWER_USERNAME || 'viewer@example.com';
const VIEWER_PASSWORD = process.env.VIEWER_PASSWORD || 'viewerpass';

export async function loginAsAdmin(page: Page) {
  const loginPage = new LoginPage(page);
  await loginPage.navigate();
  await loginPage.loginAsAdmin();
  await page.waitForURL('/');
  await page.waitForSelector('h1:has-text("Dashboard")');
}

export async function loginAsEditor(page: Page) {
  const loginPage = new LoginPage(page);
  await loginPage.navigate();
  await loginPage.loginAsEditor();
  await page.waitForURL('/');
  await page.waitForSelector('h1:has-text("Dashboard")');
}

export async function loginAsViewer(page: Page) {
  const loginPage = new LoginPage(page);
  await loginPage.navigate();
  await loginPage.loginAsViewer();
  await page.waitForURL('/');
  await page.waitForSelector('h1:has-text("Dashboard")');
}

export async function logout(page: Page) {
  const dashboardPage = new DashboardPage(page);
  await dashboardPage.logout();
}

export async function getAuthToken(request: APIRequestContext, username: string, password: string): Promise<string> {
  const baseURL = process.env.API_URL || 'http://localhost:8000';
  
  const response = await request.post(`${baseURL}/api/v1/auth/login`, {
    data: { username, password }
  });
  
  if (!response.ok()) {
    throw new Error(`Failed to get auth token: ${response.status()}`);
  }
  
  const data = await response.json();
  return data.access_token;
}

export async function setAuthToken(page: Page, token: string): Promise<void> {
  await page.goto('/');
  await page.evaluate((token) => {
    localStorage.setItem('access_token', token);
  }, token);
  await page.reload();
  await page.waitForSelector('h1:has-text("Dashboard")');
}
