import { Page } from '@playwright/test';
import { BasePage } from './BasePage';

export interface ProductFormData {
  model_number: string;
  model_name: string;
  product_type: string;
  manufacturer_id: string;
  series_id?: string;
  print_technology?: string;
  network_capable?: boolean;
  launch_date?: string;
  msrp_usd?: number;
}

/**
 * Page object for products CRUD page
 */
export class ProductsPage extends BasePage {
  // Selectors
  private readonly pageTitle = 'h1:has-text("Products")';
  private readonly createButton = '[data-testid="create-product-button"]';
  private readonly searchInput = '[data-testid="search-input"]';
  private readonly filterButton = '[data-testid="filter-button"]';
  private readonly resetFiltersButton = '[data-testid="reset-filters-button"]';
  private readonly tableRows = '[data-testid="product-row"]';
  private readonly batchDeleteButton = '[data-testid="batch-delete-button"]';
  private readonly modal = '[data-testid="crud-modal"]';
  private readonly modalSaveButton = '[data-testid="modal-save-button"]';
  private readonly modalCancelButton = '[data-testid="modal-cancel-button"]';
  private readonly paginationInfo = '[data-testid="pagination-info"]';
  private readonly nextPageButton = '[data-testid="next-page-button"]';
  private readonly prevPageButton = '[data-testid="prev-page-button"]';

  /**
   * Navigate to products page
   */
  async navigate(): Promise<void> {
    await this.goto('/products');
    await this.waitForSelector(this.pageTitle);
    // Wait for products table shell to be visible; data loading is handled by React Query
    await this.waitForSelector('[data-testid="products-table"]');
  }

  /**
   * Click create product button
   */
  async clickCreateButton(): Promise<void> {
    await this.clickTestId('create-product-button');
    // Wait for modal body content to be attached; visibility can be affected by animations
    await this.page.locator('[data-testid="crud-modal-body"]').first().waitFor({ state: 'attached' });
  }

  /**
   * Fill product form in modal
   */
  async fillProductForm(data: ProductFormData): Promise<void> {
    // Fill basic fields
    await this.fillTestId('model_number', data.model_number);
    await this.fillTestId('model_name', data.model_name);
    await this.selectTestId('product_type', data.product_type);
    await this.selectTestId('manufacturer_id', data.manufacturer_id);

    // Fill optional fields if provided
    if (data.series_id) {
      await this.selectTestId('series_id', data.series_id);
    }
    
    if (data.print_technology) {
      await this.selectTestId('print_technology', data.print_technology);
    }
    
    if (data.network_capable !== undefined) {
      const checkbox = this.page.locator('[data-testid="network_capable"]');
      if (data.network_capable) {
        await checkbox.check();
      } else {
        await checkbox.uncheck();
      }
    }
    
    if (data.launch_date) {
      await this.fillTestId('launch_date', data.launch_date);
    }
    
    if (data.msrp_usd !== undefined) {
      await this.fillTestId('msrp_usd', data.msrp_usd.toString());
    }
  }

  /**
   * Create product via modal
   */
  async createProduct(data: ProductFormData): Promise<string> {
    await this.clickCreateButton();
    await this.fillProductForm(data);

    // Wait for API response and click save
    const [response] = await Promise.all([
      this.waitForAPIResponse('/api/v1/products', 'POST'),
      this.page.locator(this.modalSaveButton).click()
    ]);

    // Wait for toast success message
    await this.waitForToast('Product created successfully');

    // Wait for modal to close
    await this.waitForElementToBeHidden(this.modal);

    // Return created product ID from response
    const responseData = await response.json();
    return responseData.data?.id || responseData.id;
  }

  /**
   * Edit existing product
   */
  async editProduct(rowIndex: number, data: Partial<ProductFormData>): Promise<void> {
    // Click row action menu (three dots)
    const row = this.page.locator(this.tableRows).nth(rowIndex);
    await row.locator('[data-testid="action-menu-button"]').click();
    
    // Click Edit menu item
    await this.clickTestId('edit-product-menu-item');
    
    // Wait for modal to open
    await this.waitForSelector(this.modal);
    
    // Fill form with partial data
    await this.fillProductForm(data as ProductFormData);
    
    // Save changes
    const [response] = await Promise.all([
      this.waitForAPIResponse(/\/api\/v1\/products\/\w+/, 'PUT'),
      this.page.locator(this.modalSaveButton).click()
    ]);

    // Wait for success message
    await this.waitForToast('Product updated successfully');
    
    // Wait for modal to close
    await this.waitForElementToBeHidden(this.modal);
  }

  /**
   * Delete product
   */
  async deleteProduct(rowIndex: number): Promise<void> {
    const row = this.page.locator(this.tableRows).nth(rowIndex);
    await row.locator('[data-testid="action-menu-button"]').click();
    
    // Click Delete menu item
    await this.clickTestId('delete-product-menu-item');
    
    // Wait for confirmation dialog and confirm
    await this.waitForSelector('[data-testid="confirm-delete-dialog"]');
    await this.clickTestId('confirm-delete-button');
    
    // Wait for API response
    await this.waitForAPIResponse(/\/api\/v1\/products\/\w+/, 'DELETE');
    
    // Wait for success message
    await this.waitForToast('Product deleted successfully');
  }

  /**
   * Search products
   */
  async searchProducts(query: string): Promise<number> {
    await this.fillTestId('search-input', query);
    
    // Wait for search API response
    await this.waitForAPIResponse(/\/api\/v1\/products\?.*search=/, 'GET');
    
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
    await this.waitForAPIResponse(/\/api\/v1\/products\?.*filter=/, 'GET');
    
    // Return filtered row count
    return this.getRowCount();
  }

  /**
   * Select manufacturer filter (cascades to series)
   */
  async selectManufacturer(manufacturerId: string): Promise<number> {
    await this.applyFilter('manufacturer_id', manufacturerId);
    
    // Wait for series options to update (cascading)
    await this.page.waitForTimeout(500);
    
    return this.getRowCount();
  }

  /**
   * Select series filter (requires manufacturer selected first)
   */
  async selectSeries(seriesId: string): Promise<number> {
    await this.applyFilter('series_id', seriesId);
    return this.getRowCount();
  }

  /**
   * Reset all filters
   */
  async resetFilters(): Promise<void> {
    await this.clickTestId('reset-filters-button');
    await this.waitForAPIResponse('/api/v1/products', 'GET');
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
   * Batch delete products
   */
  async batchDelete(rowCount: number): Promise<void> {
    await this.selectRows(rowCount);
    
    // Click batch delete button
    await this.clickTestId('batch-delete-the');
    
    // Confirm batch delete
    await this.waitForSelector('[data-testid="confirm-batch-delete-dialog"]');
    await this.clickTestId('confirm-batch-delete-button');
    
    // Wait for batch delete API response
    await this.waitForAPIResponse('/api/v1/products/batch-delete', 'DELETE');
    
    // Wait for success message
    await this.waitForToast('Products deleted successfully');
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
    await this.waitForAPIResponse(/\/api\/v1\/products\?.*page=/, 'GET');
    
    const pagination = await this.getPaginationInfo();
    return pagination.currentPage;
  }

  /**
   * Go to previous page
   */
  async goToPrevPage(): Promise<number> {
    await this.clickTestId('prev-page-button');
    await this.waitForAPIResponse(/\/api\/v1\/products\?.*page=/, 'GET');
    
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
    await this.waitForAPIResponse(/\/api\/v1\/products\?.*sort=/, 'GET');
    
    // Get sort order from aria-sort attribute
    const sortAttribute = await columnHeader.getAttribute('aria-sort');
    return sortAttribute as 'asc' | 'desc';
  }

  /**
   * Get product data from table row
   */
  async getProductData(rowIndex: number): Promise<any> {
    const row = this.page.locator(this.tableRows).nth(rowIndex);
    const cells = await row.locator('td').allTextContents();
    
    // This depends on the actual table structure
    return {
      model_number: cells[0]?.trim(),
      model_name: cells[1]?.trim(),
      product_type: cells[2]?.trim(),
      manufacturer: cells[3]?.trim(),
      series: cells[4]?.trim(),
      print_technology: cells[5]?.trim(),
      network_capable: cells[6]?.trim(),
      launch_date: cells[7]?.trim(),
      msrp_usd: cells[8]?.trim(),
      updated_at: cells[9]?.trim()
    };
  }

  /**
   * Verify products page is loaded
   */
  async isLoaded(): Promise<boolean> {
    return await this.isElementVisible(this.pageTitle) &&
           await this.isElementVisible(this.createButton) &&
           await this.isElementVisible('[data-testid="products-table"]');
  }

  /**
   * Clear search input
   */
  async clearSearch(): Promise<void> {
    await this.fillTestId('search-input', '');
    await this.waitForAPIResponse('/api/v1/products', 'GET');
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
   * Get available series for selected manufacturer
   */
  async getAvailableSeries(): Promise<string[]> {
    await this.clickTestId('filter-series_id');
    
    const options = this.page.locator('[data-testid="filter-series_id-value"] option');
    const count = await options.count();
    
    const series: string[] = [];
    for (let i = 0; i < count; i++) {
      const option = options.nth(i);
      const value = await option.getAttribute('value');
      const text = await option.textContent();
      if (value && text && value !== '') {
        series.push(text.trim());
      }
    }
    
    // Close dropdown
    await this.page.click('body');
    
    return series;
  }
}

export default ProductsPage;
