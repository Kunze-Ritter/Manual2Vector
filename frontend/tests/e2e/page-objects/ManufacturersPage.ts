import { Page } from '@playwright/test';
import { BasePage } from './BasePage';

export interface ManufacturerFormData {
  name: string;
  short_name?: string;
  country?: string;
  founded_year?: number;
  website?: string;
  support_email?: string;
  is_competitor?: boolean;
  market_share_percent?: number;
  annual_revenue_usd?: number;
  employee_count?: number;
}

/**
 * Page object for manufacturers CRUD page
 */
export class ManufacturersPage extends BasePage {
  // Selectors
  private readonly pageTitle = 'h1:has-text("Manufacturers")';
  private readonly createButton = '[data-testid="create-manufacturer-button"]';
  private readonly searchInput = '[data-testid="search-input"]';
  private readonly filterButton = '[data-testid="filter-button"]';
  private readonly resetFiltersButton = '[data-testid="reset-filters-button"]';
  private readonly tableRows = '[data-testid="manufacturer-row"]';
  private readonly batchDeleteButton = '[data-testid="batch-delete-button"]';
  private readonly modal = '[data-testid="crud-modal"]';
  private readonly modalSaveButton = '[data-testid="modal-save-button"]';
  private readonly modalCancelButton = '[data-testid="modal-cancel-button"]';
  private readonly paginationInfo = '[data-testid="pagination-info"]';
  private readonly nextPageButton = '[data-testid="next-page-button"]';
  private readonly prevPageButton = '[data-testid="prev-page-button"]';

  /**
   * Navigate to manufacturers page
   */
  async navigate(): Promise<void> {
    await this.goto('/manufacturers');
    await this.waitForSelector(this.pageTitle);
    await this.waitForAPIResponse('/api/v1/manufacturers', 'GET');
  }

  /**
   * Click create manufacturer button
   */
  async clickCreateButton(): Promise<void> {
    await this.clickTestId('create-manufacturer-button');
    await this.waitForSelector(this.modal);
  }

  /**
   * Fill manufacturer form in modal
   */
  async fillManufacturerForm(data: ManufacturerFormData): Promise<void> {
    // Fill basic fields
    await this.fillTestId('name', data.name);

    // Fill optional fields if provided
    if (data.short_name) {
      await this.fillTestId('short_name', data.short_name);
    }
    
    if (data.country) {
      await this.fillTestId('country', data.country);
    }
    
    if (data.founded_year) {
      await this.fillTestId('founded_year', data.founded_year.toString());
    }
    
    if (data.website) {
      await this.fillTestId('website', data.website);
    }
    
    if (data.support_email) {
      await this.fillTestId('support_email', data.support_email);
    }
    
    if (data.is_competitor !== undefined) {
      const checkbox = this.page.locator('[data-testid="is_competitor"]');
      if (data.is_competitor) {
        await checkbox.check();
      } else {
        await checkbox.uncheck();
      }
    }
    
    if (data.market_share_percent !== undefined) {
      await this.fillTestId('market_share_percent', data.market_share_percent.toString());
    }
    
    if (data.annual_revenue_usd !== undefined) {
      await this.fillTestId('annual_revenue_usd', data.annual_revenue_usd.toString());
    }
    
    if (data.employee_count !== undefined) {
      await this.fillTestId('employee_count', data.employee_count.toString());
    }
  }

  /**
   * Create manufacturer via modal
   */
  async createManufacturer(data: ManufacturerFormData): Promise<string> {
    await this.clickCreateButton();
    await this.fillManufacturerForm(data);

    // Wait for API response and click save
    const [response] = await Promise.all([
      this.waitForAPIResponse('/api/v1/manufacturers', 'POST'),
      this.page.locator(this.modalSaveButton).click()
    ]);

    // Wait for toast success message
    await this.waitForToast('Manufacturer created successfully');

    // Wait for modal to close
    await this.waitForElementToBeHidden(this.modal);

    // Return created manufacturer ID from response
    const responseData = await response.json();
    return responseData.data?.id || responseData.id;
  }

  /**
   * Edit existing manufacturer
   */
  async editManufacturer(rowIndex: number, data: Partial<ManufacturerFormData>): Promise<void> {
    // Click row action menu (three dots)
    const row = this.page.locator(this.tableRows).nth(rowIndex);
    await row.locator('[data-testid="action-menu-button"]').click();
    
    // Click Edit menu item
    await this.clickTestId('edit-manufacturer-menu-item');
    
    // Wait for modal to open
    await this.waitForSelector(this.modal);
    
    // Fill form with partial data
    await this.fillManufacturerForm(data as ManufacturerFormData);
    
    // Save changes
    const [response] = await Promise.all([
      this.waitForAPIResponse(/\/api\/v1\/manufacturers\/\w+/, 'PUT'),
      this.page.locator(this.modalSaveButton).click()
    ]);

    // Wait for success message
    await this.waitForToast('Manufacturer updated successfully');
    
    // Wait for modal to close
    await this.waitForElementToBeHidden(this.modal);
  }

  /**
   * Delete manufacturer
   */
  async deleteManufacturer(rowIndex: number): Promise<void> {
    const row = this.page.locator(this.tableRows).nth(rowIndex);
    await row.locator('[data-testid="action-menu-button"]').click();
    
    // Click Delete menu item
    await this.clickTestId('delete-manufacturer-menu-item');
    
    // Wait for confirmation dialog and confirm
    await this.waitForSelector('[data-testid="confirm-delete-dialog"]');
    await this.clickTestId('confirm-delete-button');
    
    // Wait for API response
    await this.waitForAPIResponse(/\/api\/v1\/manufacturers\/\w+/, 'DELETE');
    
    // Wait for success message
    await this.waitForToast('Manufacturer deleted successfully');
  }

  /**
   * Search manufacturers
   */
  async searchManufacturers(query: string): Promise<number> {
    await this.fillTestId('search-input', query);
    
    // Wait for search API response
    await this.waitForAPIResponse(/\/api\/v1\/manufacturers\?.*search=/, 'GET');
    
    // Return new row count
    return this.getRowCount();
  }

  /**
   * Apply filter
   */
  async applyFilter(filterKey: string, value: string | boolean | number): Promise<number> {
    // Open filter dropdown
    await this.clickTestId(`filter-${filterKey}`);
    
    // Select or toggle value
    if (typeof value === 'boolean') {
      // For boolean filters (checkboxes)
      const checkbox = this.page.locator(`[data-testid="filter-${filterKey}-value"]`);
      if (value) {
        await checkbox.check();
      } else {
        await checkbox.uncheck();
      }
    } else if (typeof value === 'number') {
      // For numeric range filters
      if (filterKey.includes('min_')) {
        await this.fillTestId(`filter-${filterKey}`, value.toString());
      } else if (filterKey.includes('max_')) {
        await this.fillTestId(`filter-${filterKey}`, value.toString());
      }
    } else {
      // For string/select filters
      await this.page.locator(`[data-testid="filter-${filterKey}-value"]`).selectOption(value);
    }
    
    // Wait for filter API response
    await this.waitForAPIResponse(/\/api\/v1\/manufacturers\?.*filter=/, 'GET');
    
    // Return filtered row count
    return this.getRowCount();
  }

  /**
   * Reset all filters
   */
  async resetFilters(): Promise<void> {
    await this.clickTestId('reset-filters-button');
    await this.waitForAPIResponse('/api/v1/manufacturers', 'GET');
  }

  /**
   * Select rows for batch operations
   */
  async selectRows(count: number): Promise<number> {
    for (let i = 0; i < count; i++) {
      const row = this.page.locator(this.tableRows).nth(i);
      await row.locator('[data-testid="row-checkbox"]').check();
    }
    
    // Wait for batch toolbar to appear
    await this.waitForSelector('[data-testid="batch-actions-toolbar"]');
    
    return count;
  }

  /**
   * Batch delete manufacturers
   */
  async batchDelete(rowCount: number): Promise<void> {
    await this.selectRows(rowCount);
    
    // Click batch delete button
    await this.clickTestId('batch-delete-button');
    
    // Confirm batch delete
    await this.waitForSelector('[data-testid="confirm-batch-delete-dialog"]');
    await this.clickTestId('confirm-batch-delete-button');
    
    // Wait for batch delete API response
    await this.waitForAPIResponse('/api/v1/manufacturers/batch-delete', 'DELETE');
    
    // Wait for success message
    await this.waitForToast('Manufacturers deleted successfully');
  }

  /**
   * Get table row count
   */
  async getRowCount(): Promise<number> {
    return this.getTableRowCount();
  }

  /**
   * Get pagination info
   */
  async getPaginationInfo(): Promise<any> {
    await this.waitForSelector(this.paginationInfo);
    const text = await this.getTextContent(this.paginationInfo);
    
    // Parse pagination text (e.g., "Showing 1-20 of 150 results")
    const match = text.match(/Showing (\d+)-(\d+) of (\d+) results/);
    if (match) {
      const start = parseInt(match[1], 10);
      const end = parseInt(match[2], 10);
      const total = parseInt(match[3], 10);
      const pageSize = end - start + 1;
      const currentPage = Math.ceil(start / pageSize);
      const totalPages = Math.ceil(total / pageSize);
      
      return {
        currentPage,
        totalPages,
        totalItems: total,
        pageSize
      };
    }
    
    throw new Error('Unable to parse pagination info');
  }

  /**
   * Go to next page
   */
  async goToNextPage(): Promise<number> {
    await this.clickTestId('next-page-button');
    await this.waitForAPIResponse(/\/api\/v1\/manufacturers\?.*page=/, 'GET');
    
    const pagination = await this.getPaginationInfo();
    return pagination.currentPage;
  }

  /**
   * Go to previous page
   */
  async goToPrevPage(): Promise<number> {
    await this.clickTestId('prev-page-button');
    await this.waitForAPIResponse(/\/api\/v1\/manufacturers\?.*page=/, 'GET');
    
    const pagination = await this.getPaginationInfo();
    return pagination.currentPage;
  }

  /**
   * Sort by column
   */
  async sortByColumn(columnName: string): Promise<'asc' | 'desc'> {
    // Click column header
    const columnHeader = this.page.locator(`[data-testid="column-${columnName.toLowerCase()}"]`);
    await columnHeader.click();
    
    // Wait for sort API response
    await this.waitForAPIResponse(/\/api\/v1\/manufacturers\?.*sort=/, 'GET');
    
    // Get sort order from aria-sort attribute
    const sortAttribute = await columnHeader.getAttribute('aria-sort');
    return sortAttribute as 'asc' | 'desc';
  }

  /**
   * Get manufacturer data from table row
   */
  async getManufacturerData(rowIndex: number): Promise<any> {
    const row = this.page.locator(this.tableRows).nth(rowIndex);
    const cells = await row.locator('td').allTextContents();
    
    // This depends on the actual table structure
    return {
      name: cells[0]?.trim(),
      short_name: cells[1]?.trim(),
      country: cells[2]?.trim(),
      founded_year: cells[3]?.trim(),
      website: cells[4]?.trim(),
      is_competitor: cells[5]?.trim(),
      market_share_percent: cells[6]?.trim(),
      employee_count: cells[7]?.trim(),
      created_at: cells[8]?.trim()
    };
  }

  /**
   * Verify manufacturers page is loaded
   */
  async isLoaded(): Promise<boolean> {
    return await this.isElementVisible(this.pageTitle) &&
           await this.isElementVisible(this.createButton) &&
           await this.isElementVisible('[data-testid="manufacturers-table"]');
  }

  /**
   * Clear search input
   */
  async clearSearch(): Promise<void> {
    await this.fillTestId('search-input', '');
    await this.waitForAPIResponse('/api/v1/manufacturers', 'GET');
  }

  /**
   * Open action menu for specific row
   */
  async openActionMenu(rowIndex: number): Promise<void> {
    const row = this.page.locator(this.tableRows).nth(rowIndex);
    await row.locator('[data-testid="action-menu-button"]').click();
  }

  /**
   * Check if create button is visible (for permission testing)
   */
  async isCreateButtonVisible(): Promise<boolean> {
    return this.isElementVisible(this.createButton);
  }

  /**
   * Check if edit/delete buttons are visible in action menu
   */
  async getActionMenuItems(rowIndex: number): Promise<string[]> {
    await this.openActionMenu(rowIndex);
    
    const menuItems = this.page.locator('[data-testid^="menu-item-"]');
    const count = await menuItems.count();
    
    const items: string[] = [];
    for (let i = 0; i < count; i++) {
      const item = menuItems.nth(i);
      const text = await item.textContent();
      if (text) {
        items.push(text.trim());
      }
    }
    
    // Close menu by clicking elsewhere
    await this.page.click('body');
    
    return items;
  }

  /**
   * Get available countries from filter dropdown
   */
  async getAvailableCountries(): Promise<string[]> {
    await this.clickTestId('filter-country');
    
    const options = this.page.locator('[data-testid="filter-country-value"] option');
    const count = await options.count();
    
    const countries: string[] = [];
    for (let i = 0; i < count; i++) {
      const option = options.nth(i);
      const value = await option.getAttribute('value');
      const text = await option.textContent();
      if (value && text && value !== '') {
        countries.push(text.trim());
      }
    }
    
    // Close dropdown
    await this.page.click('body');
    
    return countries;
  }
}

export default ManufacturersPage;
