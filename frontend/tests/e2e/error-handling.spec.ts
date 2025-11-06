import { test, expect } from '@playwright/test';
import { Page } from '@playwright/test';
import { LoginPage } from './page-objects/LoginPage';
import { DashboardPage } from './page-objects/DashboardPage';
import { DocumentsPage } from './page-objects/DocumentsPage';
import { ProductsPage } from './page-objects/ProductsPage';

test.describe('Error Handling', () => {
  let loginPage: LoginPage;
  let dashboardPage: DashboardPage;
  let documentsPage: DocumentsPage;
  let productsPage: ProductsPage;

  test.beforeEach(async ({ page }: { page: Page }) => {
    loginPage = new LoginPage(page);
    dashboardPage = new DashboardPage(page);
    documentsPage = new DocumentsPage(page);
    productsPage = new ProductsPage(page);
  });

  test('should handle 401 unauthorized errors gracefully', async ({ page }) => {
    // Mock 401 response for API calls
    await page.route('**/api/v1/**', route => {
      route.fulfill({
        status: 401,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Unauthorized' })
      });
    });

    await loginPage.login('admin@example.com', 'adminpass');

    // Should show user-friendly error message
    await expect(page.locator('[data-testid="error-toast"]')).toBeVisible();
    await expect(page.locator('[data-testid="error-toast"]')).toContainText('Authentication required');

    // Should redirect to login
    await expect(page).toHaveURL(/.*\/auth\/login/);
  });

  test('should handle 403 forbidden errors gracefully', async ({ page }) => {
    // Login as viewer (limited permissions)
    await loginPage.login('viewer@example.com', 'viewerpass');
    await dashboardPage.isLoaded();

    // Mock 403 for write operations
    await page.route('**/api/v1/documents**', route => {
      if (route.request().method() === 'POST') {
        route.fulfill({
          status: 403,
          contentType: 'application/json',
          body: JSON.stringify({ error: 'Forbidden - Insufficient permissions' })
        });
      } else {
        route.continue();
      }
    });

    await documentsPage.navigate();
    await documentsPage.isLoaded();

    // Try to create document (should fail)
    await documentsPage.clickCreateButton();
    await page.fill('[data-testid="filename"]', 'test.pdf');
    await page.click('[data-testid="modal-save-button"]');

    // Should show permission error
    await expect(page.locator('[data-testid="error-toast"]')).toBeVisible();
    await expect(page.locator('[data-testid="error-toast"]')).toContainText('Insufficient permissions');
  });

  test('should handle 404 not found errors gracefully', async ({ page }) => {
    await loginPage.login('admin@example.com', 'adminpass');

    // Navigate to non-existent route
    await page.goto('/non-existent-page');

    // Should show 404 page
    await expect(page.locator('[data-testid="not-found-page"]')).toBeVisible();
    await expect(page.locator('[data-testid="not-found-page"]')).toContainText('Page not found');

    // Should provide navigation back to main app
    await expect(page.locator('[data-testid="back-to-dashboard"]')).toBeVisible();
  });

  test('should handle 500 server errors gracefully', async ({ page }) => {
    // Mock 500 response
    await page.route('**/api/v1/documents', route => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Internal server error' })
      });
    });

    await loginPage.login('admin@example.com', 'adminpass');
    await documentsPage.navigate();

    // Should show server error message
    await expect(page.locator('[data-testid="error-toast"]')).toBeVisible();
    await expect(page.locator('[data-testid="error-toast"]')).toContainText('Server error');

    // Should provide retry option
    await expect(page.locator('[data-testid="retry-button"]')).toBeVisible();
  });

  test('should handle network connectivity errors', async ({ page }) => {
    await loginPage.login('admin@example.com', 'adminpass');
    await dashboardPage.isLoaded();

    // Go offline
    await page.context().setOffline(true);

    // Try to navigate to documents
    await documentsPage.navigate();

    // Should show offline error
    await expect(page.locator('[data-testid="offline-toast"]')).toBeVisible();
    await expect(page.locator('[data-testid="offline-toast"]')).toContainText('No internet connection');

    // Come back online
    await page.context().setOffline(false);

    // Should automatically retry and succeed
    await expect(page.locator('[data-testid="documents-table"]')).toBeVisible();
  });

  test('should handle timeout errors gracefully', async ({ page }) => {
    // Mock slow response
    await page.route('**/api/v1/documents', route => {
      // Don't respond to simulate timeout
      setTimeout(() => {
        route.fulfill({
          status: 408,
          contentType: 'application/json',
          body: JSON.stringify({ error: 'Request timeout' })
        });
      }, 10000);
    });

    await loginPage.login('admin@example.com', 'adminpass');
    await documentsPage.navigate();

    // Should show timeout error
    await expect(page.locator('[data-testid="error-toast"]')).toBeVisible();
    await expect(page.locator('[data-testid="error-toast"]')).toContainText('Request timeout');
  });

  test('should handle malformed API responses', async ({ page }) => {
    // Mock malformed response
    await page.route('**/api/v1/documents', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: 'invalid json response'
      });
    });

    await loginPage.login('admin@example.com', 'adminpass');
    await documentsPage.navigate();

    // Should handle parsing error gracefully
    await expect(page.locator('[data-testid="error-toast"]')).toBeVisible();
    await expect(page.locator('[data-testid="error-toast"]')).toContainText('Invalid response');
  });

  test('should handle validation errors in forms', async ({ page }) => {
    await loginPage.login('admin@example.com', 'adminpass');
    await documentsPage.navigate();
    await documentsPage.isLoaded();

    // Try to submit empty form
    await documentsPage.clickCreateButton();
    await page.click('[data-testid="modal-save-button"]');

    // Should show validation errors
    await expect(page.locator('[data-testid="validation-error"]')).toBeVisible();
    await expect(page.locator('[data-testid="validation-error"]')).toContainText('Filename is required');

    // Should highlight invalid fields
    await expect(page.locator('[data-testid="filename"]')).toHaveClass(/error/);
  });

  test('should handle concurrent request errors', async ({ page }) => {
    await loginPage.login('admin@example.com', 'adminpass');
    await documentsPage.navigate();
    await documentsPage.isLoaded();

    // Mock errors for some requests
    let requestCount = 0;
    await page.route('**/api/v1/**', route => {
      requestCount++;
      if (requestCount % 2 === 0) {
        route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({ error: 'Server error' })
        });
      } else {
        route.continue();
      }
    });

    // Make multiple concurrent requests
    await Promise.all([
      documentsPage.searchDocuments('test1'),
      documentsPage.searchDocuments('test2'),
      documentsPage.searchDocuments('test3')
    ]);

    // Should handle partial failures gracefully
    await expect(page.locator('[data-testid="documents-table"]')).toBeVisible();
    // Some error toasts might appear but app should remain functional
  });

  test('should handle file upload errors', async ({ page }) => {
    await loginPage.login('admin@example.com', 'adminpass');
    await documentsPage.navigate();
    await documentsPage.isLoaded();

    // Mock file upload error
    await page.route('**/api/v1/documents/upload', route => {
      route.fulfill({
        status: 413,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'File too large' })
      });
    });

    // Try to upload large file (if upload functionality exists)
    const fileInput = page.locator('input[type="file"]');
    if (await fileInput.isVisible()) {
      await fileInput.setInputFiles({
        name: 'large-file.pdf',
        mimeType: 'application/pdf',
        buffer: new ArrayBuffer(100 * 1024 * 1024) // 100MB
      });

      // Should show upload error
      await expect(page.locator('[data-testid="error-toast"]')).toBeVisible();
      await expect(page.locator('[data-testid="error-toast"]')).toContainText('File too large');
    }
  });

  test('should handle error recovery and retry mechanisms', async ({ page }) => {
    await loginPage.login('admin@example.com', 'adminpass');

    let failureCount = 0;
    // Mock intermittent failures
    await page.route('**/api/v1/documents', route => {
      failureCount++;
      if (failureCount <= 2) {
        route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({ error: 'Server error' })
        });
      } else {
        route.continue();
      }
    });

    await documentsPage.navigate();

    // Should show error initially
    await expect(page.locator('[data-testid="error-toast"]')).toBeVisible();

    // Click retry button
    await page.click('[data-testid="retry-button"]');

    // Should eventually succeed
    await expect(page.locator('[data-testid="documents-table"]')).toBeVisible();
    await expect(page.locator('[data-testid="error-toast"]')).not.toBeVisible();
  });

  test('should handle CORS errors gracefully', async ({ page }) => {
    // Mock CORS error
    await page.route('**/api/v1/**', route => {
      route.fulfill({
        status: 0,
        headers: {
          'Access-Control-Allow-Origin': 'https://restricted-domain.com'
        }
      });
    });

    await loginPage.login('admin@example.com', 'adminpass');

    // Should handle CORS error with user-friendly message
    await expect(page.locator('[data-testid="error-toast"]')).toBeVisible();
    await expect(page.locator('[data-testid="error-toast"]')).toContainText('Network error');
  });

  test('should maintain app state during errors', async ({ page }) => {
    await loginPage.login('admin@example.com', 'adminpass');
    await documentsPage.navigate();
    await documentsPage.isLoaded();

    // Apply some filters
    await documentsPage.applyFilter('document_type', 'service_manual');
    await documentsPage.searchDocuments('test');

    // Mock error for subsequent requests
    await page.route('**/api/v1/documents', route => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Server error' })
      });
    });

    // Try to change page (should fail)
    await page.click('[data-testid="next-page-button"]');

    // Should show error but maintain current state
    await expect(page.locator('[data-testid="error-toast"]')).toBeVisible();
    
    // Filters should remain applied
    await expect(page.locator('[data-testid="search-input"]')).toHaveValue('test');
    
    // Should be able to retry
    await page.click('[data-testid="retry-button"]');
  });
});
