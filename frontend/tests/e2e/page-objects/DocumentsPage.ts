import { Page } from '@playwright/test';
import { BasePage } from './BasePage';

export interface DocumentFormData {
  filename: string;
  original_filename: string;
  language: string;
  document_type: string;
  processing_status?: string;
  manufacturer_id?: string;
  product_id?: string;
  storage_url: string;
  publish_date?: string;
  manual_review_required?: boolean;
  manual_review_notes?: string;
}

export interface PaginationInfo {
  currentPage: number;
  totalPages: number;
  totalItems: number;
  pageSize: number;
}

/**
 * Page object for documents CRUD page
 */
export class DocumentsPage extends BasePage {
  // Selectors
  private readonly pageTitle = 'h1:has-text("Documents")';
  private readonly createButton = '[data-testid="create-document-button"]';
  private readonly searchInput = '[data-testid="search-input"]';
  private readonly filterButton = '[data-testid="filter-button"]';
  private readonly resetFiltersButton = '[data-testid="reset-filters-button"]';
  private readonly tableRows = '[data-testid="document-row"]';
  private readonly batchDeleteButton = '[data-testid="batch-delete-button"]';
  private readonly modal = '[data-testid="crud-modal"]';
  private readonly modalSaveButton = '[data-testid="modal-save-button"]';
  private readonly modalCancelButton = '[data-testid="modal-cancel-button"]';
  private readonly paginationInfo = '[data-testid="pagination-info"]';
  private readonly nextPageButton = '[data-testid="next-page-button"]';
  private readonly prevPageButton = '[data-testid="prev-page-button"]';

  /**
   * Navigate to documents page
   */
  async navigate(): Promise<void> {
    await this.goto('/documents');
    await this.waitForSelector(this.pageTitle);
    // Ensure table shell is rendered; data loading is handled by React Query
    await this.waitForSelector('[data-testid="documents-table"]');
  }

  /**
   * Click create document button
   */
  async clickCreateButton(): Promise<void> {
    await this.clickTestId('create-document-button');
    // Wait for modal body content to be attached; visibility can be affected by animations
    await this.page.locator('[data-testid="crud-modal-body"]').first().waitFor({ state: 'attached' });
  }

  /**
   * Fill document form in modal
   */
  async fillDocumentForm(data: DocumentFormData): Promise<void> {
    // Fill basic fields
    await this.fillTestId('filename', data.filename);
    await this.fillTestId('original_filename', data.original_filename);
    await this.selectTestId('language', data.language);
    await this.selectTestId('document_type', data.document_type);
    await this.fillTestId('storage_url', data.storage_url);

    // Fill optional fields if provided
    if (data.processing_status) {
      await this.selectTestId('processing_status', data.processing_status);
    }
    
    if (data.manufacturer_id) {
      await this.selectTestId('manufacturer_id', data.manufacturer_id);
    }
    
    if (data.product_id) {
      await this.selectTestId('product_id', data.product_id);
    }
    
    if (data.publish_date) {
      await this.fillTestId('publish_date', data.publish_date);
    }
    
    if (data.manual_review_required !== undefined) {
      const checkbox = this.page.locator('[data-testid="manual_review_required"]');
      if (data.manual_review_required) {
        await checkbox.check();
      } else {
        await checkbox.uncheck();
      }
    }
    
    if (data.manual_review_notes) {
      await this.fillTestId('manual_review_notes', data.manual_review_notes);
    }
  }

  /**
   * Create document via modal
   */
  async createDocument(data: DocumentFormData): Promise<string> {
    await this.clickCreateButton();
    await this.fillDocumentForm(data);

    // Wait for API response and click save
    const [response] = await Promise.all([
      this.waitForAPIResponse('/api/v1/documents', 'POST'),
      this.page.locator(this.modalSaveButton).click()
    ]);

    // Wait for toast success message
    await this.waitForToast('Document created');

    // Wait for modal to close
    await this.waitForElementToBeHidden(this.modal);

    // Return created document ID from response
    const responseData = await response.json();
    return responseData.data?.id || responseData.id;
  }

  /**
   * Edit existing document
   */
  async editDocument(rowIndex: number, data: Partial<DocumentFormData>): Promise<void> {
    // Click row action menu (three dots)
    const row = this.page.locator(this.tableRows).nth(rowIndex);
    await row.locator('[data-testid="action-menu-button"]').click();
    
    // Click Edit menu item
    await this.clickTestId('edit-document-menu-item');
    
    // Wait for modal to open
    await this.waitForSelector(this.modal);
    
    // Fill form with partial data
    await this.fillDocumentForm(data as DocumentFormData);
    
    // Save changes
    const [response] = await Promise.all([
      this.waitForAPIResponse(/\/api\/v1\/documents\/\w+/, 'PUT'),
      this.page.locator(this.modalSaveButton).click()
    ]);

    // Wait for success message
    await this.waitForToast('Document updated');
    
    // Wait for modal to close
    await this.waitForElementToBeHidden(this.modal);
  }

  /**
   * Delete document
   */
  async deleteDocument(rowIndex: number): Promise<void> {
    const row = this.page.locator(this.tableRows).nth(rowIndex);
    await row.locator('[data-testid="action-menu-button"]').click();
    
    // Click Delete menu item
    await this.clickTestId('delete-document-menu-item');
    
    // Wait for confirmation dialog and confirm
    await this.waitForSelector('[data-testid="confirm-delete-dialog"]');
    await this.clickTestId('confirm-delete-button');
    
    // Wait for API response
    await this.waitForAPIResponse(/\/api\/v1\/documents\/\w+/, 'DELETE');
    
    // Wait for success message
    await this.waitForToast('Document deleted');
  }

  /**
   * Search documents
   */
  async searchDocuments(query: string): Promise<number> {
    await this.fillTestId('search-input', query);
    
    // Wait for search API response
    await this.waitForAPIResponse(/\/api\/v1\/documents\?.*search=/, 'GET');
    
    // Return new row count
    return this.getRowCount();
  }

  /**
   * Apply filter
   */
  async applyFilter(filterKey: string, value: string | boolean): Promise<number> {
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
    } else {
      // For string/select filters
      await this.page.locator(`[data-testid="filter-${filterKey}-value"]`).selectOption(value);
    }
    
    // Wait for filter API response
    await this.waitForAPIResponse(/\/api\/v1\/documents\?.*filter=/, 'GET');
    
    // Return filtered row count
    return this.getRowCount();
  }

  /**
   * Reset all filters
   */
  async resetFilters(): Promise<void> {
    await this.clickTestId('reset-filters-button');
    await this.waitForAPIResponse('/api/v1/documents', 'GET');
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
   * Batch delete documents
   */
  async batchDelete(rowCount: number): Promise<void> {
    await this.selectRows(rowCount);
    
    // Click batch delete button
    await this.clickTestId('batch-delete-button');
    
    // Confirm batch delete
    await this.waitForSelector('[data-testid="confirm-batch-delete-dialog"]');
    await this.clickTestId('confirm-batch-delete-button');
    
    // Wait for batch delete API response
    await this.waitForAPIResponse('/api/v1/documents/batch-delete', 'DELETE');
    
    // Wait for success message
    await this.waitForToast('Batch delete completed');
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
  async getPaginationInfo(): Promise<PaginationInfo> {
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
    await this.waitForAPIResponse(/\/api\/v1\/documents\?.*page=/, 'GET');
    
    const pagination = await this.getPaginationInfo();
    return pagination.currentPage;
  }

  /**
   * Go to previous page
   */
  async goToPrevPage(): Promise<number> {
    await this.clickTestId('prev-page-button');
    await this.waitForAPIResponse(/\/api\/v1\/documents\?.*page=/, 'GET');
    
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
    await this.waitForAPIResponse(/\/api\/v1\/documents\?.*sort=/, 'GET');
    
    // Get sort order from aria-sort attribute
    const sortAttribute = await columnHeader.getAttribute('aria-sort');
    return sortAttribute as 'asc' | 'desc';
  }

  /**
   * Get document data from table row
   */
  async getDocumentData(rowIndex: number): Promise<any> {
    const row = this.page.locator(this.tableRows).nth(rowIndex);
    const cells = await row.locator('td').allTextContents();
    
    // This depends on the actual table structure
    return {
      filename: cells[0]?.trim(),
      original_filename: cells[1]?.trim(),
      document_type: cells[2]?.trim(),
      language: cells[3]?.trim(),
      processing_status: cells[4]?.trim(),
      created_at: cells[5]?.trim()
    };
  }

  /**
   * Verify documents page is loaded
   */
  async isLoaded(): Promise<boolean> {
    return await this.isElementVisible(this.pageTitle) &&
           await this.isElementVisible(this.createButton) &&
           await this.isElementVisible('[data-testid="documents-table"]');
  }

  /**
   * Clear search input
   */
  async clearSearch(): Promise<void> {
    await this.fillTestId('search-input', '');
    await this.waitForAPIResponse('/api/v1/documents', 'GET');
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
}

export default DocumentsPage;
