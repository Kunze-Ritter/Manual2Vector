import { test, expect } from '@playwright/test';
import { Page } from '@playwright/test';
import { LoginPage } from './page-objects/LoginPage';
import { DashboardPage } from './page-objects/DashboardPage';
import { DocumentsPage } from './page-objects/DocumentsPage';
import { ProductsPage } from './page-objects/ProductsPage';
import { ManufacturersPage } from './page-objects/ManufacturersPage';
import { ErrorCodesPage } from './page-objects/ErrorCodesPage';
import { VideosPage } from './page-objects/VideosPage';
import { MonitoringPage } from './page-objects/MonitoringPage';

test.describe('Navigation', () => {
  let loginPage: LoginPage;
  let dashboardPage: DashboardPage;
  let documentsPage: DocumentsPage;
  let productsPage: ProductsPage;
  let manufacturersPage: ManufacturersPage;
  let errorCodesPage: ErrorCodesPage;
  let videosPage: VideosPage;
  let monitoringPage: MonitoringPage;

  test.beforeEach(async ({ page }: { page: Page }) => {
    loginPage = new LoginPage(page);
    dashboardPage = new DashboardPage(page);
    documentsPage = new DocumentsPage(page);
    productsPage = new ProductsPage(page);
    manufacturersPage = new ManufacturersPage(page);
    errorCodesPage = new ErrorCodesPage(page);
    videosPage = new VideosPage(page);
    monitoringPage = new MonitoringPage(page);

    // Login as admin for navigation tests
    await loginPage.navigate();
    await loginPage.login('admin@example.com', 'adminpass');
    await dashboardPage.isLoaded();
  });

  test('should navigate to all main sections', async ({ page }) => {
    // Test navigation to Documents
    await dashboardPage.navigateToSection('documents');
    await documentsPage.isLoaded();
    expect(await page.textContent('h1')).toContain('Documents');

    // Test navigation to Products
    await dashboardPage.navigateToSection('products');
    await productsPage.isLoaded();
    expect(await page.textContent('h1')).toContain('Products');

    // Test navigation to Manufacturers
    await dashboardPage.navigateToSection('manufacturers');
    await manufacturersPage.isLoaded();
    expect(await page.textContent('h1')).toContain('Manufacturers');

    // Test navigation to Error Codes
    await dashboardPage.navigateToSection('error-codes');
    await errorCodesPage.isLoaded();
    expect(await page.textContent('h1')).toContain('Error Codes');

    // Test navigation to Videos
    await dashboardPage.navigateToSection('videos');
    await videosPage.isLoaded();
    expect(await page.textContent('h1')).toContain('Videos');

    // Test navigation to Monitoring
    await dashboardPage.navigateToSection('monitoring');
    await monitoringPage.isLoaded();
    expect(await page.textContent('h1')).toContain('Monitoring');
  });

  test('should show active state for current section', async ({ page }) => {
    // Test Documents active state
    await dashboardPage.navigateToSection('documents');
    const documentsNavLink = page.locator('[data-testid="nav-link-documents"]');
    await expect(documentsNavLink).toHaveClass(/active/);

    // Test Products active state
    await dashboardPage.navigateToSection('products');
    const productsNavLink = page.locator('[data-testid="nav-link-products"]');
    await expect(productsNavLink).toHaveClass(/active/);

    // Test Dashboard active state
    await dashboardPage.navigateToSection('dashboard');
    const dashboardNavLink = page.locator('[data-testid="nav-link-dashboard"]');
    await expect(dashboardNavLink).toHaveClass(/active/);
  });

  test('should provide quick actions on dashboard', async ({ page }) => {
    await dashboardPage.isLoaded();

    // Test quick action buttons exist
    await expect(page.locator('[data-testid="quick-action-new-document"]')).toBeVisible();
    await expect(page.locator('[data-testid="quick-action-new-product"]')).toBeVisible();
    await expect(page.locator('[data-testid="quick-action-new-manufacturer"]')).toBeVisible();

    // Test quick action for new document
    await page.locator('[data-testid="quick-action-new-document"]').click();
    await documentsPage.isLoaded();
    await expect(page.locator('[data-testid="create-document-button"]')).toBeVisible();
  });

  test('should handle browser navigation correctly', async ({ page }) => {
    // Navigate to Documents
    await dashboardPage.navigateToSection('documents');
    await documentsPage.isLoaded();

    // Use browser back button
    await page.goBack();
    await dashboardPage.isLoaded();

    // Use browser forward button
    await page.goForward();
    await documentsPage.isLoaded();

    // Test direct URL navigation
    await page.goto('/products');
    await productsPage.isLoaded();
  });

  test('should show auth guard for protected routes', async ({ page }) => {
    // Logout
    await loginPage.logout();

    // Try to access protected route directly
    await page.goto('/documents');
    
    // Should redirect to login
    await expect(page.locator('[data-testid="login-form"]')).toBeVisible();
    expect(page.url()).toContain('/auth/login');
  });

  test('should handle navigation with query parameters', async ({ page }) => {
    // Navigate to Documents with search query
    await page.goto('/documents?search=test&page=2');
    await documentsPage.isLoaded();

    // Verify search is applied
    await expect(page.locator('[data-testid="search-input"]')).toHaveValue('test');
    
    // Verify pagination is applied
    const paginationInfo = await documentsPage.getPaginationInfo();
    expect(paginationInfo.currentPage).toBe(2);
  });

  test('should show breadcrumb navigation on entity pages', async ({ page }) => {
    await dashboardPage.navigateToSection('documents');
    await documentsPage.isLoaded();

    // Check breadcrumb exists
    await expect(page.locator('[data-testid="breadcrumb"]')).toBeVisible();
    await expect(page.locator('[data-testid="breadcrumb-home"]')).toBeVisible();
    await expect(page.locator('[data-testid="breadcrumb-current"]')).toContainText('Documents');
  });

  test('should handle mobile navigation', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });

    // Test mobile menu toggle
    await expect(page.locator('[data-testid="mobile-menu-toggle"]')).toBeVisible();
    await page.locator('[data-testid="mobile-menu-toggle"]').click();
    
    // Mobile menu should open
    await expect(page.locator('[data-testid="mobile-menu"]')).toBeVisible();
    
    // Test navigation from mobile menu
    await page.locator('[data-testid="nav-link-products"]').click();
    await productsPage.isLoaded();
  });
});
