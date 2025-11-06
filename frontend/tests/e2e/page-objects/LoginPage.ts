import { Page } from '@playwright/test';
import { BasePage } from './BasePage';

/**
 * Page object for login page
 */
export class LoginPage extends BasePage {
  // Selectors
  private readonly usernameInput = '[data-testid="username"]';
  private readonly passwordInput = '[data-testid="password"]';
  private readonly loginButton = '[data-testid="login-button"]';
  private readonly rememberMeCheckbox = '[data-testid="remember-me-checkbox"]';
  private readonly errorAlert = '[data-testid="login-error-alert"]';
  private readonly registerLink = '[data-testid="register-link"]';

  /**
   * Navigate to login page
   */
  async navigate(): Promise<void> {
    await this.goto('/login');
    await this.waitForSelector(this.usernameInput);
  }

  /**
   * Login with username and password
   */
  async login(username: string, password: string, rememberMe = false): Promise<any> {
    // Fill credentials
    await this.fillTestId('username', username);
    await this.fillTestId('password', password);

    // Set remember me if requested
    if (rememberMe) {
      await this.page.locator(this.rememberMeCheckbox).check();
    }

    // Wait for and click login button
    const [response] = await Promise.all([
      this.waitForAPIResponse('/api/v1/auth/login', 'POST'),
      this.page.locator(this.loginButton).click()
    ]);

    // Wait for navigation to dashboard
    await this.page.waitForURL('/');
    await this.waitForNavigation();

    // Return response data for verification
    return response.json();
  }

  /**
   * Logout current user
   */
  async logout(): Promise<void> {
    // Click user menu/avatar if visible
    const userMenu = this.page.locator('[data-testid="user-menu-button"]');
    if (await userMenu.isVisible()) {
      await userMenu.click();
      // Click logout option
      await this.clickTestId('logout-button');
    } else {
      // Fallback: navigate directly to logout endpoint
      await this.goto('/auth/logout');
    }
    
    // Wait for redirect to login page
    await this.page.waitForURL(/.*\/auth\/login/);
  }

  /**
   * Login as admin user
   */
  async loginAsAdmin(): Promise<any> {
    const username = 'admin@example.com';
    const password = 'adminpass';
    return this.login(username, password);
  }

  /**
   * Login as editor user
   */
  async loginAsEditor(): Promise<any> {
    const username = 'editor@example.com';
    const password = 'editorpass';
    return this.login(username, password);
  }

  /**
   * Login as viewer user
   */
  async loginAsViewer(): Promise<any> {
    const username = 'viewer@example.com';
    const password = 'viewerpass';
    return this.login(username, password);
  }

  /**
   * Get error message if visible
   */
  async getErrorMessage(): Promise<string> {
    if (await this.isElementVisible(this.errorAlert)) {
      const text = await this.getTextContent(this.errorAlert);
      return text || '';
    }
    return '';
  }

  /**
   * Check if login button is disabled
   */
  async isLoginButtonDisabled(): Promise<boolean> {
    const button = this.page.locator(this.loginButton);
    return await button.isDisabled();
  }

  /**
   * Click register link
   */
  async clickRegisterLink(): Promise<void> {
    await this.page.locator(this.registerLink).click();
    await this.page.waitForURL('/register');
  }

  /**
   * Verify login page is loaded
   */
  async isLoaded(): Promise<boolean> {
    return await this.isElementVisible(this.usernameInput) && 
           await this.isElementVisible(this.passwordInput) &&
           await this.isElementVisible(this.loginButton);
  }

  /**
   * Get current form values
   */
  async getFormValues(): Promise<{ username: string; password: string; rememberMe: boolean }> {
    const username = await this.page.locator(this.usernameInput).inputValue();
    const password = await this.page.locator(this.passwordInput).inputValue();
    const rememberMe = await this.page.locator(this.rememberMeCheckbox).isChecked();
    
    return { username, password, rememberMe };
  }

  /**
   * Clear form
   */
  async clearForm(): Promise<void> {
    await this.page.locator(this.usernameInput).fill('');
    await this.page.locator(this.passwordInput).fill('');
    await this.page.locator(this.rememberMeCheckbox).uncheck();
  }

  /**
   * Submit form without filling credentials (for testing validation)
   */
  async submitEmptyForm(): Promise<void> {
    await this.clearForm();
    await this.page.locator(this.loginButton).click();
  }

  /**
   * Check if user is redirected to login (unauthorized access)
   */
  async isAtLogin(): Promise<boolean> {
    const currentUrl = await this.getCurrentUrl();
    return currentUrl.includes('/login');
  }

  /**
   * Wait for login to complete (successful)
   */
  async waitForLoginSuccess(): Promise<void> {
    await this.page.waitForURL('/');
    await this.waitForSelector('h1:has-text("Dashboard")');
  }

  /**
   * Wait for login to fail (error message appears)
   */
  async waitForLoginError(): Promise<string> {
    await this.waitForSelector(this.errorAlert);
    return this.getErrorMessage();
  }
}

export default LoginPage;
