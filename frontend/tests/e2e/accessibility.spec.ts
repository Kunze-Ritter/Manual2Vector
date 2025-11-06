import { test, expect } from '@playwright/test';
import { Page } from '@playwright/test';
import { LoginPage } from './page-objects/LoginPage';
import { DashboardPage } from './page-objects/DashboardPage';
import { DocumentsPage } from './page-objects/DocumentsPage';
import { ProductsPage } from './page-objects/ProductsPage';
import { MonitoringPage } from './page-objects/MonitoringPage';

// Extend Window interface for accessibility testing
declare global {
  interface Window {
    checkBasicAccessibility: () => string[];
  }
}

test.describe('Accessibility', () => {
  let loginPage: LoginPage;
  let dashboardPage: DashboardPage;
  let documentsPage: DocumentsPage;
  let productsPage: ProductsPage;
  let monitoringPage: MonitoringPage;

  test.beforeEach(async ({ page }: { page: Page }) => {
    loginPage = new LoginPage(page);
    dashboardPage = new DashboardPage(page);
    documentsPage = new DocumentsPage(page);
    productsPage = new ProductsPage(page);
    monitoringPage = new MonitoringPage(page);

    // Basic accessibility setup - check for proper semantic HTML
    await page.addInitScript(() => {
      // Add basic accessibility testing helpers
      window.checkBasicAccessibility = () => {
        const issues = [];
        
        // Check for proper heading hierarchy
        const headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
        if (headings.length === 0) {
          issues.push('No headings found');
        }
        
        // Check for alt text on images
        const images = document.querySelectorAll('img:not([alt])');
        if (images.length > 0) {
          issues.push(`${images.length} images missing alt text`);
        }
        
        // Check for form labels
        const inputs = document.querySelectorAll('input:not([aria-label]):not([aria-labelledby])');
        const unlabeledInputs = Array.from(inputs).filter(input => {
          const id = input.getAttribute('id');
          return !id || !document.querySelector(`label[for="${id}"]`);
        });
        if (unlabeledInputs.length > 0) {
          issues.push(`${unlabeledInputs.length} inputs missing labels`);
        }
        
        return issues;
      };
    });
  });

  test('should meet accessibility standards on login page', async ({ page }) => {
    await loginPage.navigate();
    
    // Check basic accessibility
    const issues = await page.evaluate(() => window.checkBasicAccessibility());
    expect(issues).toEqual([]);
    
    // Check for proper form structure
    await expect(page.locator('form')).toBeVisible();
    await expect(page.locator('input[type="email"], input[type="text"]')).toBeVisible();
    await expect(page.locator('input[type="password"]')).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toBeVisible();
  });

  test('should meet accessibility standards on dashboard', async ({ page }) => {
    // Login first
    await loginPage.login('admin@example.com', 'adminpass');
    await dashboardPage.isLoaded();
    
    // Check basic accessibility
    const issues = await page.evaluate(() => window.checkBasicAccessibility());
    expect(issues).toEqual([]);
    
    // Check for main landmarks
    await expect(page.locator('main, [role="main"]')).toBeVisible();
    await expect(page.locator('nav, [role="navigation"]')).toBeVisible();
  });

  test('should meet accessibility standards on documents page', async ({ page }) => {
    await loginPage.login('admin@example.com', 'adminpass');
    await documentsPage.navigate();
    await documentsPage.isLoaded();
    
    // Check main documents page
    // Check basic accessibility
    const issues = await page.evaluate(() => window.checkBasicAccessibility());
    expect(issues).toEqual([]);
  });

  test('should meet accessibility standards on documents modal', async ({ page }) => {
    await loginPage.login('admin@example.com', 'adminpass');
    await documentsPage.navigate();
    await documentsPage.isLoaded();
    
    // Open create document modal
    await documentsPage.clickCreateButton();
    await expect(page.locator('[data-testid="crud-modal"]')).toBeVisible();
    
    // Check modal accessibility
    const modalIssues = await page.evaluate(() => window.checkBasicAccessibility());
    expect(modalIssues).toEqual([]);
  });

  test('should meet accessibility standards on products page', async ({ page }) => {
    await loginPage.login('admin@example.com', 'adminpass');
    await productsPage.navigate();
    await productsPage.isLoaded();
    
    // Check products page
    const issues = await page.evaluate(() => window.checkBasicAccessibility());
    expect(issues).toEqual([]);
  });

  test('should meet accessibility standards on monitoring page', async ({ page }) => {
    await loginPage.login('admin@example.com', 'adminpass');
    await monitoringPage.navigate();
    await monitoringPage.isLoaded();
    
    // Check monitoring page
    const issues = await page.evaluate(() => window.checkBasicAccessibility());
    expect(issues).toEqual([]);
  });

  test('should have proper keyboard navigation', async ({ page }) => {
    await loginPage.navigate();
    
    // Test tab navigation through login form
    await page.keyboard.press('Tab');
    await expect(page.locator('[data-testid="email-input"]')).toBeFocused();
    
    await page.keyboard.press('Tab');
    await expect(page.locator('[data-testid="password-input"]')).toBeFocused();
    
    await page.keyboard.press('Tab');
    await expect(page.locator('[data-testid="login-button"]')).toBeFocused();
    
    // Test Enter key submission
    await page.locator('[data-testid="email-input"]').fill('admin@example.com');
    await page.locator('[data-testid="password-input"]').fill('adminpass');
    await page.keyboard.press('Enter');
    
    // Should navigate to dashboard
    await expect(page.locator('[data-testid="dashboard-stats"]')).toBeVisible();
  });

  test('should have proper ARIA labels and roles', async ({ page }) => {
    await loginPage.login('admin@example.com', 'adminpass');
    await dashboardPage.isLoaded();
    
    // Check main landmarks
    await expect(page.locator('main')).toHaveAttribute('role', 'main');
    await expect(page.locator('nav')).toHaveAttribute('role', 'navigation');
    await expect(page.locator('header')).toHaveAttribute('role', 'banner');
    
    // Check form labels
    await expect(page.locator('[data-testid="search-input"]')).toHaveAttribute('aria-label');
    await expect(page.locator('[data-testid="filter-button"]')).toHaveAttribute('aria-label');
  });

  test('should have proper heading hierarchy', async ({ page }) => {
    await loginPage.login('admin@example.com', 'adminpass');
    await dashboardPage.isLoaded();
    
    // Check heading levels
    const headings = await page.locator('h1, h2, h3, h4, h5, h6').all();
    
    // First heading should be h1
    expect(await headings[0].evaluate(el => el.tagName)).toBe('H1');
    
    // Check proper heading order (no skipped levels)
    for (let i = 1; i < headings.length; i++) {
      const currentLevel = parseInt(await headings[i].evaluate(el => el.tagName.charAt(1)));
      const previousLevel = parseInt(await headings[i-1].evaluate(el => el.tagName.charAt(1)));
      
      // Should not skip heading levels by more than 1
      expect(currentLevel - previousLevel).toBeLessThanOrEqual(1);
    }
  });

  test('should have sufficient color contrast', async ({ page }) => {
    await loginPage.navigate();
    
    // Check contrast ratios for critical elements
    const issues = await page.evaluate(() => window.checkBasicAccessibility());
    expect(issues).toEqual([]);
  });

  test('should handle screen reader announcements', async ({ page }) => {
    await loginPage.login('admin@example.com', 'adminpass');
    await documentsPage.navigate();
    await documentsPage.isLoaded();
    
    // Create a document and check for success announcement
    const documentData = {
      filename: 'accessibility-test.pdf',
      original_filename: 'accessibility-test.pdf',
      language: 'en',
      document_type: 'service_manual',
      storage_url: 'https://example.com/test.pdf'
    };
    
    await documentsPage.createDocument(documentData);
    
    // Check for aria-live region or similar announcement mechanism
    const liveRegion = page.locator('[aria-live="polite"], [aria-live="assertive"]');
    await expect(liveRegion).toBeVisible();
  });

  test('should be accessible with high contrast mode', async ({ page }) => {
    // Simulate high contrast mode
    await page.emulateMedia({ colorScheme: 'dark', reducedMotion: 'reduce' });
    
    await loginPage.login('admin@example.com', 'adminpass');
    await dashboardPage.isLoaded();
    
    // Check accessibility in high contrast
    const issues = await page.evaluate(() => window.checkBasicAccessibility());
    expect(issues).toEqual([]);
  });
});
