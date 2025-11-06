import { Page } from '@playwright/test';
import { BasePage } from './BasePage';

export interface VideoFormData {
  title: string;
  url: string;
  platform: 'youtube' | 'vimeo' | 'brightcove';
  youtube_id?: string;
  vimeo_id?: string;
  duration_seconds?: number;
  view_count?: number;
  manufacturer_id?: string;
  series_id?: string;
  document_id?: string;
  thumbnail_url?: string;
  published_at?: string;
}

/**
 * Page object for videos CRUD page
 */
export class VideosPage extends BasePage {
  // Selectors
  private readonly pageTitle = 'h1:has-text("Videos")';
  private readonly createButton = '[data-testid="create-video-button"]';
  private readonly searchInput = '[data-testid="search-input"]';
  private readonly filterButton = '[data-testid="filter-button"]';
  private readonly resetFiltersButton = '[data-testid="reset-filters-button"]';
  private readonly tableRows = '[data-testid="video-row"]';
  private readonly batchDeleteButton = '[data-testid="batch-delete-button"]';
  private readonly modal = '[data-testid="crud-modal"]';
  private readonly modalSaveButton = '[data-testid="modal-save-button"]';
  private readonly modalCancelButton = '[data-testid="modal-cancel-button"]';
  private readonly paginationInfo = '[data-testid="pagination-info"]';
  private readonly nextPageButton = '[data-testid="next-page-button"]';
  private readonly prevPageButton = '[data-testid="prev-page-button"]';

  /**
   * Navigate to videos page
   */
  async navigate(): Promise<void> {
    await this.goto('/videos');
    await this.waitForSelector(this.pageTitle);
    await this.waitForAPIResponse('/api/v1/videos', 'GET');
  }

  /**
   * Click create video button
   */
  async clickCreateButton(): Promise<void> {
    await this.clickTestId('create-video-button');
    await this.waitForSelector(this.modal);
  }

  /**
   * Fill video form in modal
   */
  async fillVideoForm(data: VideoFormData): Promise<void> {
    // Fill basic fields
    await this.fillTestId('title', data.title);
    await this.fillTestId('url', data.url);
    await this.selectTestId('platform', data.platform);

    // Fill platform-specific fields
    if (data.platform === 'youtube' && data.youtube_id) {
      await this.fillTestId('youtube_id', data.youtube_id);
    } else if (data.platform === 'vimeo' && data.vimeo_id) {
      await this.fillTestId('vimeo_id', data.vimeo_id);
    }

    // Fill optional fields if provided
    if (data.duration_seconds !== undefined) {
      await this.fillTestId('duration_seconds', data.duration_seconds.toString());
    }
    
    if (data.view_count !== undefined) {
      await this.fillTestId('view_count', data.view_count.toString());
    }
    
    if (data.manufacturer_id) {
      await this.selectTestId('manufacturer_id', data.manufacturer_id);
    }
    
    if (data.series_id) {
      await this.selectTestId('series_id', data.series_id);
    }
    
    if (data.document_id) {
      await this.selectTestId('document_id', data.document_id);
    }
    
    if (data.thumbnail_url) {
      await this.fillTestId('thumbnail_url', data.thumbnail_url);
    }
    
    if (data.published_at) {
      await this.fillTestId('published_at', data.published_at);
    }
  }

  /**
   * Create video via modal
   */
  async createVideo(data: VideoFormData): Promise<string> {
    await this.clickCreateButton();
    await this.fillVideoForm(data);

    // Wait for API response and click save
    const [response] = await Promise.all([
      this.waitForAPIResponse('/api/v1/videos', 'POST'),
      this.page.locator(this.modalSaveButton).click()
    ]);

    // Wait for toast success message
    await this.waitForToast('Video created successfully');

    // Wait for modal to close
    await this.waitForElementToBeHidden(this.modal);

    // Return created video ID from response
    const responseData = await response.json();
    return responseData.data?.id || responseData.id;
  }

  /**
   * Edit existing video
   */
  async editVideo(rowIndex: number, data: Partial<VideoFormData>): Promise<void> {
    // Click row action menu (three dots)
    const row = this.page.locator(this.tableRows).nth(rowIndex);
    await row.locator('[data-testid="action-menu-button"]').click();
    
    // Click Edit menu item
    await this.clickTestId('edit-video-menu-item');
    
    // Wait for modal to open
    await this.waitForSelector(this.modal);
    
    // Fill form with partial data
    await this.fillVideoForm(data as VideoFormData);
    
    // Save changes
    const [response] = await Promise.all([
      this.waitForAPIResponse(/\/api\/v1\/videos\/\w+/, 'PUT'),
      this.page.locator(this.modalSaveButton).click()
    ]);

    // Wait for success message
    await this.waitForToast('Video updated successfully');
    
    // Wait for modal to close
    await this.waitForElementToBeHidden(this.modal);
  }

  /**
   * Delete video
   */
  async deleteVideo(rowIndex: number): Promise<void> {
    const row = this.page.locator(this.tableRows).nth(rowIndex);
    await row.locator('[data-testid="action-menu-button"]').click();
    
    // Click Delete menu item
    await this.clickTestId('delete-video-menu-item');
    
    // Wait for confirmation dialog and confirm
    await this.waitForSelector('[data-testid="confirm-delete-dialog"]');
    await this.clickTestId('confirm-delete-button');
    
    // Wait for API response
    await this.waitForAPIResponse(/\/api\/v1\/videos\/\w+/, 'DELETE');
    
    // Wait for success message
    await this.waitForToast('Video deleted successfully');
  }

  /**
   * Search videos
   */
  async searchVideos(query: string): Promise<number> {
    await this.fillTestId('search-input', query);
    
    // Wait for search API response
    await this.waitForAPIResponse(/\/api\/v1\/videos\?.*search=/, 'GET');
    
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
    await this.waitForAPIResponse(/\/api\/v1\/videos\?.*filter=/, 'GET');
    
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
    await this.waitForAPIResponse('/api/v1/videos', 'GET');
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
   * Batch delete videos
   */
  async batchDelete(rowCount: number): Promise<void> {
    await this.selectRows(rowCount);
    
    // Click batch delete button
    await this.clickTestId('batch-delete-button');
    
    // Confirm batch delete
    await this.waitForSelector('[data-testid="confirm-batch-delete-dialog"]');
    await this.clickTestId('confirm-batch-delete-button');
    
    // Wait for batch delete API response
    await this.waitForAPIResponse('/api/v1/videos/batch-delete', 'DELETE');
    
    // Wait for success message
    await this.waitForToast('Videos deleted successfully');
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
    await this.waitForAPIResponse(/\/api\/v1\/videos\?.*page=/, 'GET');
    
    const pagination = await this.getPaginationInfo();
    return pagination.currentPage;
  }

  /**
   * Go to previous page
   */
  async goToPrevPage(): Promise<number> {
    await this.clickTestId('prev-page-button');
    await this.waitForAPIResponse(/\/api\/v1\/videos\?.*page=/, 'GET');
    
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
    await this.waitForAPIResponse(/\/api\/v1\/videos\?.*sort=/, 'GET');
    
    // Get sort order from aria-sort attribute
    const sortAttribute = await columnHeader.getAttribute('aria-sort');
    return sortAttribute as 'asc' | 'desc';
  }

  /**
   * Get video data from table row
   */
  async getVideoData(rowIndex: number): Promise<any> {
    const row = this.page.locator(this.tableRows).nth(rowIndex);
    const cells = await row.locator('td').allTextContents();
    
    // This depends on the actual table structure
    return {
      title: cells[0]?.trim(),
      platform: cells[1]?.trim(),
      youtube_id: cells[2]?.trim(),
      duration: cells[3]?.trim(),
      view_count: cells[4]?.trim(),
      manufacturer: cells[5]?.trim(),
      series: cells[6]?.trim(),
      document: cells[7]?.trim(),
      published_at: cells[8]?.trim(),
      created_at: cells[9]?.trim()
    };
  }

  /**
   * Get video thumbnail URL from row
   */
  async getVideoThumbnail(rowIndex: number): Promise<string> {
    const row = this.page.locator(this.tableRows).nth(rowIndex);
    const thumbnail = row.locator('[data-testid="video-thumbnail"]');
    
    // Check if thumbnail image exists
    const imgElement = thumbnail.locator('img');
    if (await imgElement.isVisible()) {
      return await imgElement.getAttribute('src') || '';
    }
    
    // Return placeholder if no image
    return '';
  }

  /**
   * Get video duration from row
   */
  async getVideoDuration(rowIndex: number): Promise<string> {
    const row = this.page.locator(this.tableRows).nth(rowIndex);
    const durationElement = row.locator('[data-testid="video-duration"]');
    return await durationElement.textContent() || '';
  }

  /**
   * Verify videos page is loaded
   */
  async isLoaded(): Promise<boolean> {
    return await this.isElementVisible(this.pageTitle) &&
           await this.isElementVisible(this.createButton) &&
           await this.isElementVisible('[data-testid="videos-table"]');
  }

  /**
   * Clear search input
   */
  async clearSearch(): Promise<void> {
    await this.fillTestId('search-input', '');
    await this.waitForAPIResponse('/api/v1/videos', 'GET');
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
   * Get available platforms from filter dropdown
   */
  async getAvailablePlatforms(): Promise<string[]> {
    await this.clickTestId('filter-platform');
    
    const options = this.page.locator('[data-testid="filter-platform-value"] option');
    const count = await options.count();
    
    const platforms: string[] = [];
    for (let i = 0; i < count; i++) {
      const option = options.nth(i);
      const value = await option.getAttribute('value');
      const text = await option.textContent();
      if (value && text && value !== '') {
        platforms.push(text.trim());
      }
    }
    
    // Close dropdown
    await this.page.click('body');
    
    return platforms;
  }

  /**
   * Filter by platform
   */
  async filterByPlatform(platform: string): Promise<number> {
    return this.applyFilter('platform', platform);
  }

  /**
   * Filter by YouTube ID
   */
  async filterByYouTubeId(youtubeId: string): Promise<number> {
    return this.applyFilter('youtube_id', youtubeId);
  }

  /**
   * Verify thumbnail display
   */
  async verifyThumbnailDisplay(rowIndex: number, hasThumbnail: boolean): Promise<boolean> {
    const thumbnailUrl = await this.getVideoThumbnail(rowIndex);
    
    if (hasThumbnail) {
      // Should have a valid thumbnail URL
      return thumbnailUrl !== '' && thumbnailUrl.startsWith('http');
    } else {
      // Should show placeholder icon
      const row = this.page.locator(this.tableRows).nth(rowIndex);
      const placeholder = row.locator('[data-testid="thumbnail-placeholder"]');
      return await placeholder.isVisible();
    }
  }

  /**
   * Verify duration formatting
   */
  async verifyDurationFormatting(rowIndex: number): Promise<boolean> {
    const duration = await this.getVideoDuration(rowIndex);
    
    // Check if duration is formatted as MM:SS or HH:MM:SS
    return /^(\d{1,2}:)?\d{1,2}:\d{2}$/.test(duration);
  }
}

export default VideosPage;
