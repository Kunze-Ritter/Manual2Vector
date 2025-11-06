import { Page, Locator, Response } from '@playwright/test';

/**
 * Base page object class with common functionality for all page objects
 */
export class BasePage {
  readonly page: Page;
  readonly baseURL: string;

  constructor(page: Page) {
    this.page = page;
    this.baseURL = process.env.BASE_URL || 'http://localhost:3000';
  }

  /**
   * Navigate to a path relative to baseURL
   */
  async goto(path: string): Promise<Page> {
    await this.page.goto(`${this.baseURL}${path}`);
    await this.page.waitForLoadState('networkidle');
    return this.page;
  }

  /**
   * Wait for element to be visible
   */
  async waitForSelector(selector: string, options?: { timeout?: number }): Promise<Locator> {
    const timeout = options?.timeout || 10000;
    await this.page.waitForSelector(selector, { state: 'visible', timeout });
    return this.page.locator(selector);
  }

  /**
   * Wait for element with data-testid to be visible
   */
  async waitForTestId(testId: string, options?: { timeout?: number }): Promise<Locator> {
    const timeout = options?.timeout || 10000;
    return this.waitForSelector(`[data-testid="${testId}"]`, { timeout });
  }

  /**
   * Click element with data-testid
   */
  async clickTestId(testId: string): Promise<void> {
    await this.waitForTestId(testId);
    await this.page.locator(`[data-testid="${testId}"]`).click();
  }

  /**
   * Fill input with data-testid
   */
  async fillTestId(testId: string, value: string): Promise<void> {
    await this.waitForTestId(testId);
    await this.page.locator(`[data-testid="${testId}"]`).fill(value);
  }

  /**
   * Select option in dropdown with data-testid
   */
  async selectTestId(testId: string, value: string): Promise<void> {
    await this.waitForTestId(testId);
    await this.page.locator(`[data-testid="${testId}"]`).selectOption(value);
  }

  /**
   * Get text content of element
   */
  async getTextContent(selector: string): Promise<string> {
    const element = await this.waitForSelector(selector);
    const text = await element.textContent();
    return text?.trim() || '';
  }

  /**
   * Wait for toast notification with specific message
   */
  async waitForToast(message: string, timeout = 5000): Promise<boolean> {
    try {
      await this.page.waitForSelector(`[role="status"]:has-text("${message}")`, { timeout });
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Wait for API response matching pattern
   */
  async waitForAPIResponse(urlPattern: string | RegExp, method = 'GET'): Promise<Response> {
    return this.page.waitForResponse(resp => 
      (resp.url().match(urlPattern) || resp.url().includes(urlPattern as string)) &&
      resp.request().method() === method
    );
  }

  /**
   * Take screenshot with descriptive name
   */
  async takeScreenshot(name: string): Promise<void> {
    await this.page.screenshot({ 
      path: `test-results/screenshots/${name}-${Date.now()}.png`,
      fullPage: true 
    });
  }

  /**
   * Count visible table rows (excluding header)
   */
  async getTableRowCount(): Promise<number> {
    const rows = await this.page.locator('[data-testid="table-row"]').count();
    return rows;
  }

  /**
   * Check if element is visible
   */
  async isElementVisible(selector: string): Promise<boolean> {
    try {
      await this.page.waitForSelector(selector, { state: 'visible', timeout: 2000 });
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Wait for navigation to complete
   */
  async waitForNavigation(): Promise<void> {
    await this.page.waitForLoadState('networkidle');
  }

  /**
   * Get current URL
   */
  async getCurrentUrl(): Promise<string> {
    return this.page.url();
  }

  /**
   * Wait for element to be hidden
   */
  async waitForElementToBeHidden(selector: string, timeout = 10000): Promise<void> {
    await this.page.waitForSelector(selector, { state: 'hidden', timeout });
  }

  /**
   * Check if element exists
   */
  async elementExists(selector: string): Promise<boolean> {
    const count = await this.page.locator(selector).count();
    return count > 0;
  }

  /**
   * Hover over element with data-testid
   */
  async hoverTestId(testId: string): Promise<void> {
    await this.waitForTestId(testId);
    await this.page.locator(`[data-testid="${testId}"]`).hover();
  }

  /**
   * Get attribute value from element
   */
  async getAttribute(selector: string, attribute: string): Promise<string | null> {
    const element = await this.page.locator(selector).first();
    return element.getAttribute(attribute);
  }

  /**
   * Wait for multiple elements to be visible
   */
  async waitForSelectors(selectors: string[], timeout = 10000): Promise<Locator[]> {
    const locators: Locator[] = [];
    for (const selector of selectors) {
      const locator = await this.waitForSelector(selector, { timeout });
      locators.push(locator);
    }
    return locators;
  }
}

export default BasePage;
