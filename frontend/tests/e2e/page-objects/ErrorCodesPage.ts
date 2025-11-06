import { Page } from '@playwright/test';
import { BasePage } from './BasePage';

export interface ErrorCodeFormData {
  error_code: string;
  error_description: string;
  severity_level: 'critical' | 'high' | 'medium' | 'low' | 'info';
  manufacturer_id?: string;
  document_id?: string;
  chunk_id?: string;
  requires_technician?: boolean;
  requires_parts?: boolean;
  estimated_fix_time_minutes?: number;
  solution_steps?: string;
}

/**
 * Page object for error codes CRUD page
 */
export class ErrorCodesPage extends BasePage {
  // Selectors
  private readonly pageTitle = 'h1:has-text("Error Codes")';
  private readonly createButton = '[data-testid="create-error-code-button"]';
  private readonly searchInput = '[data-testid="search-input"]';
  private readonly filterButton = '[data-testid="filter-button"]';
  private readonly resetFiltersButton = '[data-testid="reset-filters-button"]';
  private readonly tableRows = '[data-testid="error-code-row"]';
  private readonly batchDeleteButton = '[data-testid="batch-delete-button"]';
  private readonly modal = '[data-testid="crud-modal"]';
  private readonly modalSaveButton = '[data-testid="modal-save-button"]';
  private readonly modalCancelButton = '[data-testid="modal-cancel-button"]';
  private readonly paginationInfo = '[data-testid="pagination-info"]';
  private readonly nextPageButton = '[data-testid="next-page-button"]';
  private readonly prevPageButton = '[data-testid="prev-page-button"]';

  /**
   * Navigate to error codes page
   */
  async navigate(): Promise<void> {
    await this.goto('/error-codes');
    await this.waitForSelector(this.pageTitle);
    await this.waitForAPIResponse('/api/v1/error-codes', 'GET');
  }

  /**
   * Click create error code button
   */
  async clickCreateButton(): Promise<void> {
    await this.clickTestId('create-error-code-button');
    await this.waitForSelector(this.modal);
  }

  /**
   * Fill error code form in modal
   */
  async fillErrorCodeForm(data: ErrorCodeFormData): Promise<void> {
    // Fill basic fields
    await this.fillTestId('error_code', data.error_code);
    await this.fillTestId('error_description', data.error_description);
    await this.selectTestId('severity_level', data.severity_level);

    // Fill optional fields if provided
    if (data.manufacturer_id) {
      await this.selectTestId('manufacturer_id', data.manufacturer_id);
    }
    
    if (data.document_id) {
      await this.selectTestId('document_id', data.document_id);
    }
    
    if (data.chunk_id) {
      await this.selectTestId('chunk_id', data.chunk_id);
    }
    
    if (data.requires_technician !== undefined) {
      const checkbox = this.page.locator('[data-testid="requires_technician"]');
      if (data.requires_technician) {
        await checkbox.check();
      } else {
        await checkbox.uncheck();
      }
    }
    
    if (data.requires_parts !== undefined) {
      const checkbox = this.page.locator('[data-testid="requires_parts"]');
      if (data.requires_parts) {
        await checkbox.check();
      } else {
        await checkbox.uncheck();
      }
    }
    
    if (data.estimated_fix_time_minutes !== undefined) {
      await this.fillTestId('estimated_fix_time_minutes', data.estimated_fix_time_minutes.toString());
    }
    
    if (data.solution_steps) {
      await this.fillTestId('solution_steps', data.solution_steps);
    }
  }

  /**
   * Create error code via modal
   */
  async createErrorCode(data: ErrorCodeFormData): Promise<string> {
    await this.clickCreateButton();
    await this.fillErrorCodeForm(data);

    // Wait for API response and click save
    const [response] = await Promise.all([
      this.waitForAPIResponse('/api/v1/error-codes', 'POST'),
      this.page.locator(this.modalSaveButton).click()
    ]);

    // Wait for toast success message
    await this.waitForToast('Error code created successfully');

    // Wait for modal to close
    await this.waitForElementToBeHidden(this.modal);

    // Return created error code ID from response
    const responseData = await response.json();
    return responseData.data?.id || responseData.id;
  }

  /**
   * Edit existing error code
   */
  async editErrorCode(rowIndex: number, data: Partial<ErrorCodeFormData>): Promise<void> {
    // Click row action menu (three dots)
    const row = this.page.locator(this.tableRows).nth(rowIndex);
    await row.locator('[data-testid="action-menu-button"]').click();
    
    // Click Edit menu item
    await this.clickTestId('edit-error-code-menu-item');
    
    // Wait for modal to open
    await this.waitForSelector(this.modal);
    
    // Fill form with partial data
    await this.fillErrorCodeForm(data as ErrorCodeFormData);
    
    // Save changes
    const [response] = await Promise.all([
      this.waitForAPIResponse(/\/api\/v1\/error-codes\/\w+/, 'PUT'),
      this.page.locator(this.modalSaveButton).click()
    ]);

    // Wait for success message
    await this.waitForToast('Error code updated successfully');
    
    // Wait for modal to close
    await this.waitForElementToBeHidden(this.modal);
  }

  /**
   * Delete error code
   */
  async deleteErrorCode(rowIndex: number): Promise<void> {
    const row = this.page.locator(this.tableRows).nth(rowIndex);
    await row.locator('[data-testid="action-menu-button"]').click();
    
    // Click Delete menu item
    await this.clickTestId('delete-error-code-menu-item');
    
    // Wait for confirmation dialog and confirm
    await this.waitForSelector('[data-testid="confirm-delete-dialog"]');
    await this.clickTestId('confirm-delete-button');
    
    // Wait for API response
    await this.waitForAPIResponse(/\/api\/v1\/error-codes\/\w+/, 'DELETE');
    
    // Wait for success message
    await this.waitForToast('Error code deleted successfully');
  }

  /**
   * Search error codes
   */
  async searchErrorCodes(query: string): Promise<number> {
    await this.fillTestId('search-input', query);
    
    // Wait for search API response
    await this.waitForAPIResponse(/\/api\/v1\/error-codes\?.*search=/, 'GET');
    
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
    await this.waitForAPIResponse(/\/api\/v1\/error-codes\?.*filter=/, 'GET');
    
    // Return filtered row count
    return this.getRowCount();
  }

  /**
   * Reset all filters
   */
  async resetFilters(): Promise<void> {
    await this.clickTestId('reset-filters-button');
    await this.waitForAPIResponse('/api/v1/error-codes', 'GET');
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
   * Batch delete error codes
   */
  async batchDelete(rowCount: number): Promise<void> {
    await this.selectRows(rowCount);
    
    // Click batch delete button
    await this.clickTestId('batch-delete-button');
    
    // Confirm batch delete
    await this.waitForSelector('[data-testid="confirm-batch-delete-dialog"]');
    await this.clickTestId('confirm-batch-delete-button');
    
    // Wait for batch delete API response
    await this.waitForAPIResponse('/api/v1/error-codes/batch-delete', 'DELETE');
    
    // Wait for success message
    await this.waitForToast('Error codes deleted successfully');
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
    await this.waitForAPIResponse(/\/api\/v1\/error-codes\?.*page=/, 'GET');
    
    const pagination = await this.getPaginationInfo();
    return pagination.currentPage;
  }

  /**
   * Go to previous page
   */
  async goToPrevPage(): Promise<number> {
    await this.clickTestId('prev-page-button');
    await this.waitForAPIResponse(/\/api\/v1\/error-codes\?.*page=/, 'GET');
    
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
    await this.waitForAPIResponse(/\/api\/v1\/error-codes\?.*sort=/, 'GET');
    
    // Get sort order from aria-sort attribute
    const sortAttribute = await columnHeader.getAttribute('aria-sort');
    return sortAttribute as 'asc' | 'desc';
  }

  /**
   * Get error code data from table row
   */
  async getErrorCodeData(rowIndex: number): Promise<any> {
    const row = this.page.locator(this.tableRows).nth(rowIndex);
    const cells = await row.locator('td').allTextContents();
    
    // This depends on the actual table structure
    return {
      error_code: cells[0]?.trim(),
      error_description: cells[1]?.trim(),
      severity_level: cells[2]?.trim(),
      manufacturer: cells[3]?.trim(),
      document: cells[4]?.trim(),
      requires_technician: cells[5]?.trim(),
      requires_parts: cells[6]?.trim(),
      estimated_fix_time_minutes: cells[7]?.trim(),
      created_at: cells[8]?.trim()
    };
  }

  /**
   * Verify error codes page is loaded
   */
  async isLoaded(): Promise<boolean> {
    return await this.isElementVisible(this.pageTitle) &&
           await this.isElementVisible(this.createButton) &&
           await this.isElementVisible('[data-testid="error-codes-table"]');
  }

  /**
   * Clear search input
   */
  async clearSearch(): Promise<void> {
    await this.fillTestId('search-input', '');
    await this.waitForAPIResponse('/api/v1/error-codes', 'GET');
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
   * Get available manufacturers from filter dropdown
   */
  async getAvailableManufacturers(): Promise<string[]> {
    await this.clickTestId('filter-manufacturer_id');
    
    const options = this.page.locator('[data-testid="filter-manufacturer_id-value"] option');
    const count = await options.count();
    
    const manufacturers: string[] = [];
    for (let i = 0; i < count; i++) {
      const option = options.nth(i);
      const value = await option.getAttribute('value');
      const text = await option.textContent();
      if (value && text && value !== '') {
        manufacturers.push(text.trim());
      }
    }
    
    // Close dropdown
    await this.page.click('body');
    
    return manufacturers;
  }

  /**
   * Get available severity levels from filter dropdown
   */
  async getAvailableSeverityLevels(): Promise<string[]> {
    await this.clickTestId('filter-severity_level');
    
    const options = this.page.locator('[data-testid="filter-severity_level-value"] option');
    const count = await options.count();
    
    const severities: string[] = [];
    for (let i = 0; i < count; i++) {
      const option = options.nth(i);
      const value = await option.getAttribute('value');
      const text = await option.textContent();
      if (value && text && value !== '') {
        severities.push(text.trim());
      }
    }
    
    // Close dropdown
    await this.page.click('body');
    
    return severities;
  }

  /**
   * Filter by severity level
   */
  async filterBySeverity(severity: string): Promise<number> {
    return this.applyFilter('severity_level', severity);
  }

  /**
   * Filter by requires technician
   */
  async filterByRequiresTechnician(requires: boolean): Promise<number> {
    return this.applyFilter('requires_technician', requires);
  }

  /**
   * Filter by requires parts
   */
  async filterByRequiresParts(requires: boolean): Promise<number> {
    return this.applyFilter('requires_parts', requires);
  }
}

export default ErrorCodesPage;
