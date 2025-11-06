import { test, expect } from '@playwright/test';
import { Page } from '@playwright/test';
import { LoginPage } from './page-objects/LoginPage';
import { DashboardPage } from './page-objects/DashboardPage';
import { DocumentsPage } from './page-objects/DocumentsPage';
import { ProductsPage } from './page-objects/ProductsPage';

test.describe('Visual Regression', () => {
  let loginPage: LoginPage;
  let dashboardPage: DashboardPage;
  let documentsPage: DocumentsPage;
  let productsPage: ProductsPage;

  test.beforeEach(async ({ page }: { page: Page }) => {
    loginPage = new LoginPage(page);
    dashboardPage = new DashboardPage(page);
    documentsPage = new DocumentsPage(page);
    productsPage = new ProductsPage(page);

    // Set consistent viewport for visual tests
    await page.setViewportSize({ width: 1280, height: 720 });
  });

  test('should match login page screenshot', async ({ page }) => {
    await loginPage.navigate();
    await loginPage.isLoaded();

    // Take full page screenshot
    await expect(page).toHaveScreenshot('login-page.png', {
      fullPage: true,
      animations: 'disabled',
      clip: { x: 0, y: 0, width: 1280, height: 720 }
    });
  });

  test('should match dashboard screenshot', async ({ page }) => {
    await loginPage.login('admin@example.com', 'adminpass');
    await dashboardPage.isLoaded();

    // Wait for all dynamic content to load
    await page.waitForSelector('[data-testid="dashboard-stats"]');
    await page.waitForSelector('[data-testid="quick-actions"]');
    await page.waitForSelector('[data-testid="recent-activity"]');

    await expect(page).toHaveScreenshot('dashboard.png', {
      fullPage: true,
      animations: 'disabled'
    });
  });

  test('should match documents page screenshot', async ({ page }) => {
    await loginPage.login('admin@example.com', 'adminpass');
    await documentsPage.navigate();
    await documentsPage.isLoaded();

    // Wait for table to load
    await page.waitForSelector('[data-testid="documents-table"]');
    await page.waitForSelector('[data-testid="table-row"]');

    await expect(page).toHaveScreenshot('documents-page.png', {
      fullPage: true,
      animations: 'disabled'
    });
  });

  test('should match documents modal screenshot', async ({ page }) => {
    await loginPage.login('admin@example.com', 'adminpass');
    await documentsPage.navigate();
    await documentsPage.isLoaded();

    // Open create document modal
    await documentsPage.clickCreateButton();
    await page.waitForSelector('[data-testid="crud-modal"]');

    // Take modal screenshot
    await expect(page.locator('[data-testid="crud-modal"]')).toHaveScreenshot('documents-modal.png', {
      animations: 'disabled'
    });
  });

  test('should match products page screenshot', async ({ page }) => {
    await loginPage.login('admin@example.com', 'adminpass');
    await productsPage.navigate();
    await productsPage.isLoaded();

    // Wait for table to load
    await page.waitForSelector('[data-testid="products-table"]');
    await page.waitForSelector('[data-testid="table-row"]');

    await expect(page).toHaveScreenshot('products-page.png', {
      fullPage: true,
      animations: 'disabled'
    });
  });

  test('should match filter bar screenshot', async ({ page }) => {
    await loginPage.login('admin@example.com', 'adminpass');
    await documentsPage.navigate();
    await documentsPage.isLoaded();

    // Take filter bar screenshot
    await expect(page.locator('[data-testid="filter-bar"]')).toHaveScreenshot('filter-bar.png', {
      animations: 'disabled'
    });
  });

  test('should match batch actions toolbar screenshot', async ({ page }) => {
    await loginPage.login('admin@example.com', 'adminpass');
    await documentsPage.navigate();
    await documentsPage.isLoaded();

    // Select some rows to show batch toolbar
    await documentsPage.selectRows(2);
    await page.waitForSelector('[data-testid="batch-actions-toolbar"]');

    // Take batch toolbar screenshot
    await expect(page.locator('[data-testid="batch-actions-toolbar"]')).toHaveScreenshot('batch-actions-toolbar.png', {
      animations: 'disabled'
    });
  });

  test('should match confirmation dialog screenshot', async ({ page }) => {
    await loginPage.login('admin@example.com', 'adminpass');
    await documentsPage.navigate();
    await documentsPage.isLoaded();

    // Open delete confirmation dialog
    await documentsPage.openActionMenu(0);
    await documentsPage.deleteDocument(0);

    // Take dialog screenshot (before confirmation)
    await expect(page.locator('[data-testid="confirm-delete-dialog"]')).toHaveScreenshot('delete-confirmation-dialog.png', {
      animations: 'disabled'
    });
  });

  test('should match responsive mobile screenshots', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });

    await loginPage.login('admin@example.com', 'adminpass');
    await dashboardPage.isLoaded();

    // Take mobile dashboard screenshot
    await expect(page).toHaveScreenshot('dashboard-mobile.png', {
      fullPage: true,
      animations: 'disabled'
    });

    // Navigate to documents on mobile
    await dashboardPage.navigateToSection('documents');
    await documentsPage.isLoaded();

    // Take mobile documents screenshot
    await expect(page).toHaveScreenshot('documents-mobile.png', {
      fullPage: true,
      animations: 'disabled'
    });
  });

  test('should match dark mode screenshots', async ({ page }) => {
    // Enable dark mode
    await page.emulateMedia({ colorScheme: 'dark' });

    await loginPage.login('admin@example.com', 'adminpass');
    await dashboardPage.isLoaded();

    // Take dark mode dashboard screenshot
    await expect(page).toHaveScreenshot('dashboard-dark.png', {
      fullPage: true,
      animations: 'disabled'
    });

    // Navigate to documents in dark mode
    await dashboardPage.navigateToSection('documents');
    await documentsPage.isLoaded();

    // Take dark mode documents screenshot
    await expect(page).toHaveScreenshot('documents-dark.png', {
      fullPage: true,
      animations: 'disabled'
    });
  });

  test('should match table screenshots with different states', async ({ page }) => {
    await loginPage.login('admin@example.com', 'adminpass');
    await documentsPage.navigate();
    await documentsPage.isLoaded();

    // Screenshot with empty state (if applicable)
    await documentsPage.searchDocuments('nonexistent');
    await page.waitForTimeout(1000);

    const hasEmptyState = await page.locator('[data-testid="table-empty-state"]').isVisible();
    if (hasEmptyState) {
      await expect(page.locator('[data-testid="documents-table"]')).toHaveScreenshot('documents-empty-state.png', {
        animations: 'disabled'
      });
    }

    // Clear search and get normal state
    await documentsPage.clearSearch();

    // Screenshot with selected rows
    await documentsPage.selectRows(2);
    await expect(page.locator('[data-testid="documents-table"]')).toHaveScreenshot('documents-selected-rows.png', {
      animations: 'disabled'
    });
  });

  test('should match loading state screenshots', async ({ page }) => {
    await loginPage.login('admin@example.com', 'adminpass');

    // Intercept API to simulate loading
    await page.route('**/api/v1/documents', route => {
      setTimeout(() => route.continue(), 2000); // Add delay
    });

    await documentsPage.navigate();

    // Take loading screenshot
    await expect(page.locator('[data-testid="documents-table"]')).toHaveScreenshot('documents-loading.png', {
      animations: 'disabled'
    });
  });

  test('should match hover state screenshots', async ({ page }) => {
    await loginPage.login('admin@example.com', 'adminpass');
    await documentsPage.navigate();
    await documentsPage.isLoaded();

    // Hover over create button
    await page.hover('[data-testid="create-document-button"]');
    await expect(page.locator('[data-testid="create-document-button"]')).toHaveScreenshot('create-button-hover.png', {
      animations: 'disabled'
    });

    // Hover over table row
    const firstRow = page.locator('[data-testid="table-row"]').first();
    await firstRow.hover();
    await expect(firstRow).toHaveScreenshot('table-row-hover.png', {
      animations: 'disabled'
    });
  });

  test('should match focus state screenshots', async ({ page }) => {
    await loginPage.navigate();

    // Focus on email input
    await page.focus('[data-testid="email-input"]');
    await expect(page.locator('[data-testid="email-input"]')).toHaveScreenshot('email-input-focus.png', {
      animations: 'disabled'
    });

    // Focus on password input
    await page.focus('[data-testid="password-input"]');
    await expect(page.locator('[data-testid="password-input"]')).toHaveScreenshot('password-input-focus.png', {
      animations: 'disabled'
    });
  });

  test('should match error state screenshots', async ({ page }) => {
    await loginPage.navigate();

    // Try to login with invalid credentials to show error state
    await loginPage.login('invalid@example.com', 'invalidpassword');

    // Wait for error message
    await page.waitForSelector('[data-testid="error-message"]');

    // Take error state screenshot
    await expect(page.locator('[data-testid="login-form"]')).toHaveScreenshot('login-error-state.png', {
      animations: 'disabled'
    });
  });
});
