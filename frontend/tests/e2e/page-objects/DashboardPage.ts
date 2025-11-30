import { Page } from '@playwright/test';
import { BasePage } from './BasePage';

export interface StatCard {
  label: string;
  value: string | number;
}

/**
 * Page object for dashboard/home page
 */
export class DashboardPage extends BasePage {
  // Selectors
  private readonly pageTitle = 'h1:has-text("Dashboard")';
  private readonly statsCards = '[data-testid^="stat-card-"]';
  private readonly quickActionsSection = '[data-testid="quick-actions"]';
  private readonly navigationSection = '[data-testid="navigation-overview"]';
  private readonly sidebar = 'aside';
  private readonly userMenu = '[data-testid="user-menu"]';
  private readonly logoutButton = '[data-testid="logout-button"]';

  /**
   * Navigate to dashboard
   */
  async navigate(): Promise<void> {
    await this.goto('/');
    await this.waitForSelector(this.pageTitle);
  }

  /**
   * Get stat value by label (e.g., 'Total Documents')
   */
  async getStatValue(label: string): Promise<number> {
    const statCardSelector = `[data-testid="stat-card-${label.toLowerCase().replace(/\s+/g, '-')}"]`;
    await this.waitForSelector(statCardSelector);
    
    const statCard = this.page.locator(statCardSelector);
    const text = await statCard.textContent();
    
    // Extract numeric value from text (e.g., "150 Documents" -> 150)
    const numericValue = text?.match(/\d+/)?.[0] || '0';
    return parseInt(numericValue, 10);
  }

  /**
   * Get all stat cards
   */
  async getAllStats(): Promise<StatCard[]> {
    await this.waitForSelector(this.statsCards);
    const cards = this.page.locator(this.statsCards);
    const count = await cards.count();
    
    const stats: StatCard[] = [];
    for (let i = 0; i < count; i++) {
      const card = cards.nth(i);
      const text = await card.textContent() || '';
      
      // Extract label and value from card text
      const lines = text.split('\n').filter(line => line.trim());
      if (lines.length >= 2) {
        const value = lines[0].trim();
        const label = lines[1].trim();
        
        stats.push({
          label,
          value: value
        });
      }
    }
    
    return stats;
  }

  /**
   * Click quick action button by label
   */
  async clickQuickAction(label: string): Promise<void> {
    const quickActionSelector = `[data-testid="quick-action-${label.toLowerCase().replace(/\s+/g, '-')}"]`;
    await this.clickTestId(quickActionSelector.replace('[data-testid="', '').replace('"]', ''));
  }

  /**
   * Navigate to section via navigation overview
   */
  async navigateToSection(section: string): Promise<string> {
    const testId = `nav-link-${section.toLowerCase().replace(/\s+/g, '-')}`;
    await this.clickTestId(testId);
    await this.waitForNavigation();
    
    return this.getCurrentUrl();
  }

  /**
   * Get user role from sidebar
   */
  async getUserRole(): Promise<string> {
    await this.waitForSelector(this.sidebar);
    const roleElement = this.page.locator('[data-testid="user-role"]');
    const roleText = await roleElement.textContent();
    return roleText?.toLowerCase().trim() || '';
  }

  /**
   * Logout user
   */
  async logout(): Promise<void> {
    // Click user menu to expand
    await this.page.locator(this.userMenu).click();
    
    // Wait for logout button to be visible
    await this.waitForSelector(this.logoutButton);
    
    // Click logout button
    await this.page.locator(this.logoutButton).click();
    
    // Wait for navigation to login
    await this.page.waitForURL('/login');
    
    // Verify token cleared from localStorage
    const token = await this.page.evaluate(() => localStorage.getItem('access_token'));
    if (token !== null) {
      throw new Error('Token not cleared from localStorage after logout');
    }
  }

  /**
   * Check if sidebar is visible
   */
  async isSidebarVisible(): Promise<boolean> {
    return this.isElementVisible(this.sidebar);
  }

  /**
   * Get all visible navigation items from sidebar
   */
  async getSidebarNavigationItems(): Promise<string[]> {
    await this.waitForSelector(this.sidebar);
    const navLinks = this.page.locator('aside a[href*="/"]');
    const count = await navLinks.count();
    
    const items: string[] = [];
    for (let i = 0; i < count; i++) {
      const link = navLinks.nth(i);
      const text = await link.textContent();
      if (text && text.trim()) {
        items.push(text.trim());
      }
    }
    
    return items;
  }

  /**
   * Verify dashboard is fully loaded
   */
  async isLoaded(): Promise<boolean> {
    return await this.isElementVisible(this.pageTitle) &&
           await this.isElementVisible(this.statsCards) &&
           await this.isElementVisible(this.quickActionsSection);
  }

  /**
   * Get quick action buttons
   */
  async getQuickActions(): Promise<string[]> {
    await this.waitForSelector(this.quickActionsSection);
    const buttons = this.page.locator(`${this.quickActionsSection} button`);
    const count = await buttons.count();
    
    const actions: string[] = [];
    for (let i = 0; i < count; i++) {
      const button = buttons.nth(i);
      const text = await button.textContent();
      if (text && text.trim()) {
        actions.push(text.trim());
      }
    }
    
    return actions;
  }

  /**
   * Get navigation overview cards
   */
  async getNavigationCards(): Promise<string[]> {
    await this.waitForSelector(this.navigationSection);
    const cards = this.page.locator(`${this.navigationSection} [data-testid^="nav-item-"]`);
    const count = await cards.count();
    
    const navigation: string[] = [];
    for (let i = 0; i < count; i++) {
      const card = cards.nth(i);
      const text = await card.textContent();
      if (text && text.trim()) {
        navigation.push(text.trim());
      }
    }
    
    return navigation;
  }

  /**
   * Wait for stats to load (API calls complete)
   */
  async waitForStatsToLoad(): Promise<void> {
    // Wait for stat cards to be visible and have content
    await this.waitForSelector(this.statsCards);
    await this.page.waitForFunction(() => {
      const cards = document.querySelectorAll('[data-testid="stat-card"]');
      return Array.from(cards).every(card => card.textContent && card.textContent.trim().length > 0);
    });
  }

  /**
   * Check if specific stat card exists
   */
  async hasStatCard(label: string): Promise<boolean> {
    const statCardSelector = `[data-testid="stat-card-${label.toLowerCase().replace(/\s+/g, '-')}"]`;
    return this.elementExists(statCardSelector);
  }

  /**
   * Get user info from sidebar
   */
  async getUserInfo(): Promise<{ name: string; email: string; role: string }> {
    await this.waitForSelector('[data-testid="user-info"]');
    
    const userInfo = this.page.locator('[data-testid="user-info"]');
    const text = await userInfo.textContent() || '';
    
    // Parse user info (this may need adjustment based on actual UI structure)
    const lines = text.split('\n').filter(line => line.trim());
    
    return {
      name: lines[0]?.trim() || '',
      email: lines[1]?.trim() || '',
      role: lines[2]?.trim() || ''
    };
  }

  /**
   * Click logo to navigate to dashboard
   */
  async clickLogo(): Promise<void> {
    await this.page.locator('a[href="/"]').click();
    await this.waitForNavigation();
  }
}

export default DashboardPage;
