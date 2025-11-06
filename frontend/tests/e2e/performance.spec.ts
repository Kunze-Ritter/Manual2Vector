import { test, expect } from '@playwright/test';
import { Page } from '@playwright/test';
import { LoginPage } from './page-objects/LoginPage';
import { DashboardPage } from './page-objects/DashboardPage';
import { DocumentsPage } from './page-objects/DocumentsPage';
import { ProductsPage } from './page-objects/ProductsPage';

test.describe('Performance', () => {
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

  test('should load login page within performance thresholds', async ({ page }) => {
    const startTime = Date.now();
    
    await loginPage.navigate();
    await loginPage.isLoaded();
    
    const loadTime = Date.now() - startTime;
    
    // Page should load within 3 seconds
    expect(loadTime).toBeLessThan(3000);
    
    // Check Core Web Vitals
    const performanceMetrics = await page.evaluate(() => {
      const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
      return {
        domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
        loadComplete: navigation.loadEventEnd - navigation.loadEventStart,
        firstPaint: performance.getEntriesByType('paint').find(p => p.name === 'first-paint')?.startTime || 0,
        firstContentfulPaint: performance.getEntriesByType('paint').find(p => p.name === 'first-contentful-paint')?.startTime || 0,
      };
    });
    
    // First Contentful Paint should be under 2 seconds
    expect(performanceMetrics.firstContentfulPaint).toBeLessThan(2000);
    
    // DOM Content Loaded should be under 1.5 seconds
    expect(performanceMetrics.domContentLoaded).toBeLessThan(1500);
  });

  test('should load dashboard within performance thresholds', async ({ page }) => {
    await loginPage.login('admin@example.com', 'adminpass');
    
    const startTime = Date.now();
    await dashboardPage.isLoaded();
    const loadTime = Date.now() - startTime;
    
    // Dashboard should load within 3 seconds
    expect(loadTime).toBeLessThan(3000);
    
    // Check that all dashboard components are loaded
    await expect(page.locator('[data-testid="dashboard-stats"]')).toBeVisible();
    await expect(page.locator('[data-testid="quick-actions"]')).toBeVisible();
    await expect(page.locator('[data-testid="recent-activity"]')).toBeVisible();
  });

  test('should load documents page within performance thresholds', async ({ page }) => {
    await loginPage.login('admin@example.com', 'adminpass');
    
    const startTime = Date.now();
    await documentsPage.navigate();
    await documentsPage.isLoaded();
    const loadTime = Date.now() - startTime;
    
    // Documents page should load within 3 seconds
    expect(loadTime).toBeLessThan(3000);
    
    // Table should be rendered
    await expect(page.locator('[data-testid="documents-table"]')).toBeVisible();
  });

  test('should handle API response times within thresholds', async ({ page }) => {
    await loginPage.login('admin@example.com', 'adminpass');
    
    // Monitor API responses
    const apiResponseTimes: number[] = [];
    
    page.on('response', async (response) => {
      if (response.url().includes('/api/v1/')) {
        const timing = response.request().timing();
        const responseTime = timing.responseEnd - timing.requestStart;
        apiResponseTimes.push(responseTime);
      }
    });
    
    await documentsPage.navigate();
    await documentsPage.isLoaded();
    
    // API responses should be under 500ms on average
    if (apiResponseTimes.length > 0) {
      const averageResponseTime = apiResponseTimes.reduce((a, b) => a + b, 0) / apiResponseTimes.length;
      expect(averageResponseTime).toBeLessThan(500);
    }
  });

  test('should handle large datasets efficiently', async ({ page }) => {
    await loginPage.login('admin@example.com', 'adminpass');
    await documentsPage.navigate();
    
    // Test pagination performance
    const startTime = Date.now();
    
    // Navigate through multiple pages
    for (let i = 1; i <= 3; i++) {
      await documentsPage.goToNextPage();
      await expect(page.locator('[data-testid="documents-table"]')).toBeVisible();
    }
    
    const paginationTime = Date.now() - startTime;
    
    // Pagination should be responsive (under 2 seconds for 3 page changes)
    expect(paginationTime).toBeLessThan(2000);
  });

  test('should handle search performance efficiently', async ({ page }) => {
    await loginPage.login('admin@example.com', 'adminpass');
    await documentsPage.navigate();
    await documentsPage.isLoaded();
    
    // Test search performance
    const startTime = Date.now();
    await documentsPage.searchDocuments('test');
    const searchTime = Date.now() - startTime;
    
    // Search should complete within 1 second
    expect(searchTime).toBeLessThan(1000);
    
    // Results should be displayed
    await expect(page.locator('[data-testid="documents-table"]')).toBeVisible();
  });

  test('should handle filter operations efficiently', async ({ page }) => {
    await loginPage.login('admin@example.com', 'adminpass');
    await documentsPage.navigate();
    await documentsPage.isLoaded();
    
    // Test filter performance
    const startTime = Date.now();
    await documentsPage.applyFilter('document_type', 'service_manual');
    const filterTime = Date.now() - startTime;
    
    // Filter should apply within 1 second
    expect(filterTime).toBeLessThan(1000);
  });

  test('should handle memory usage efficiently', async ({ page }) => {
    await loginPage.login('admin@example.com', 'adminpass');
    
    // Check initial memory usage
    const initialMemory = await page.evaluate(() => {
      return (performance as any).memory?.usedJSHeapSize || 0;
    });
    
    // Perform multiple operations
    await dashboardPage.isLoaded();
    await documentsPage.navigate();
    await documentsPage.isLoaded();
    await productsPage.navigate();
    await productsPage.isLoaded();
    
    // Check memory after operations
    const finalMemory = await page.evaluate(() => {
      return (performance as any).memory?.usedJSHeapSize || 0;
    });
    
    // Memory growth should be reasonable (less than 50MB)
    const memoryGrowth = finalMemory - initialMemory;
    expect(memoryGrowth).toBeLessThan(50 * 1024 * 1024); // 50MB
  });

  test('should handle concurrent operations efficiently', async ({ page }) => {
    await loginPage.login('admin@example.com', 'adminpass');
    await documentsPage.navigate();
    await documentsPage.isLoaded();
    
    // Perform multiple concurrent operations
    const startTime = Date.now();
    
    await Promise.all([
      documentsPage.searchDocuments('test'),
      documentsPage.applyFilter('document_type', 'service_manual'),
      page.waitForResponse('**/api/v1/documents**')
    ]);
    
    const concurrentTime = Date.now() - startTime;
    
    // Concurrent operations should complete efficiently
    expect(concurrentTime).toBeLessThan(2000);
  });

  test('should handle render performance with large tables', async ({ page }) => {
    await loginPage.login('admin@example.com', 'adminpass');
    await documentsPage.navigate();
    
    // Measure table render time
    const startTime = Date.now();
    
    await page.waitForSelector('[data-testid="documents-table"]');
    await page.waitForSelector('[data-testid="table-row"]');
    
    const renderTime = Date.now() - startTime;
    
    // Table should render within 2 seconds
    expect(renderTime).toBeLessThan(2000);
  });

  test('should debounce search input properly', async ({ page }) => {
    await loginPage.login('admin@example.com', 'adminpass');
    await documentsPage.navigate();
    await documentsPage.isLoaded();
    
    let apiCallCount = 0;
    
    page.on('response', (response) => {
      if (response.url().includes('/api/v1/documents') && response.url().includes('search')) {
        apiCallCount++;
      }
    });
    
    // Type multiple characters quickly
    const searchInput = page.locator('[data-testid="search-input"]');
    await searchInput.fill('test search query');
    
    // Wait for debounced API calls to complete
    await page.waitForTimeout(500);
    
    // Should not make excessive API calls (debouncing should work)
    expect(apiCallCount).toBeLessThan(5);
  });

  test('should maintain performance under load', async ({ page }) => {
    await loginPage.login('admin@example.com', 'adminpass');
    await documentsPage.navigate();
    await documentsPage.isLoaded();
    
    // Simulate heavy usage
    const startTime = Date.now();
    
    for (let i = 0; i < 10; i++) {
      await documentsPage.searchDocuments(`test ${i}`);
      await page.waitForTimeout(100);
    }
    
    const totalTime = Date.now() - startTime;
    
    // Average operation time should remain reasonable
    const averageTime = totalTime / 10;
    expect(averageTime).toBeLessThan(500);
  });
});
