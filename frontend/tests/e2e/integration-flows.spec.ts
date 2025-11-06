import { test, expect } from '@playwright/test';
import { Page } from '@playwright/test';
import { LoginPage } from './page-objects/LoginPage';
import { DashboardPage } from './page-objects/DashboardPage';
import { DocumentsPage } from './page-objects/DocumentsPage';
import { ProductsPage } from './page-objects/ProductsPage';
import { ManufacturersPage } from './page-objects/ManufacturersPage';
import { ErrorCodesPage } from './page-objects/ErrorCodesPage';
import { VideosPage } from './page-objects/VideosPage';
import { MonitoringPage } from './page-objects/MonitoringPage';
import { createTestManufacturer, createTestProduct, createTestDocument, createTestErrorCode, createTestVideo } from './fixtures/test-data.fixture';

test.describe('Integration Flows', () => {
  let loginPage: LoginPage;
  let dashboardPage: DashboardPage;
  let documentsPage: DocumentsPage;
  let productsPage: ProductsPage;
  let manufacturersPage: ManufacturersPage;
  let errorCodesPage: ErrorCodesPage;
  let videosPage: VideosPage;
  let monitoringPage: MonitoringPage;

  test.beforeEach(async ({ page, request }: { page: Page, request: any }) => {
    loginPage = new LoginPage(page);
    dashboardPage = new DashboardPage(page);
    documentsPage = new DocumentsPage(page);
    productsPage = new ProductsPage(page);
    manufacturersPage = new ManufacturersPage(page);
    errorCodesPage = new ErrorCodesPage(page);
    videosPage = new VideosPage(page);
    monitoringPage = new MonitoringPage(page);

    // Login as admin
    await loginPage.navigate();
    await loginPage.login('admin@example.com', 'adminpass');
    await dashboardPage.isLoaded();
  });

  test('should complete full manufacturer -> product -> document workflow', async ({ page, request }) => {
    // Step 1: Create manufacturer
    await dashboardPage.navigateToSection('manufacturers');
    await manufacturersPage.isLoaded();

    const manufacturerData = {
      name: 'Integration Test Manufacturer',
      short_name: 'INTTEST',
      country: 'USA',
      website: 'https://inttest.com'
    };

    await manufacturersPage.clickCreateButton();
    await manufacturersPage.fillManufacturerForm(manufacturerData);
    const manufacturerId = await manufacturersPage.createManufacturer(manufacturerData);

    // Verify manufacturer created
    await expect(page.locator('[data-testid="success-toast"]')).toContainText('Manufacturer created');
    await manufacturersPage.isLoaded();

    // Step 2: Create product linked to manufacturer
    await dashboardPage.navigateToSection('products');
    await productsPage.isLoaded();

    const productData = {
      model_number: 'INT-TEST-001',
      model_name: 'Integration Test Product',
      product_type: 'printer',
      manufacturer_id: manufacturerId,
      network_capable: true
    };

    await productsPage.clickCreateButton();
    await productsPage.fillProductForm(productData);
    const productId = await productsPage.createProduct(productData);

    // Verify product created and linked
    await expect(page.locator('[data-testid="success-toast"]')).toContainText('Product created');
    await productsPage.isLoaded();

    // Step 3: Create document linked to product
    await dashboardPage.navigateToSection('documents');
    await documentsPage.isLoaded();

    const documentData = {
      filename: 'int-test-manual.pdf',
      original_filename: 'int-test-manual.pdf',
      language: 'en',
      document_type: 'service_manual',
      product_id: productId,
      manufacturer_id: manufacturerId,
      storage_url: 'https://example.com/int-test-manual.pdf'
    };

    await documentsPage.createDocument(documentData);

    // Verify document created and linked
    await expect(page.locator('[data-testid="success-toast"]')).toContainText('Document created');
    await documentsPage.isLoaded();

    // Step 4: Verify relationships in data
    await documentsPage.searchDocuments('int-test-manual');
    const rowCount = await documentsPage.getRowCount();
    expect(rowCount).toBeGreaterThan(0);

    // Step 5: Clean up (reverse order)
    await documentsPage.deleteDocument(0);
    await dashboardPage.navigateToSection('products');
    await productsPage.navigate();
    await productsPage.deleteProduct(0);
    await dashboardPage.navigateToSection('manufacturers');
    await manufacturersPage.navigate();
    await manufacturersPage.deleteManufacturer(0);
  });

  test('should complete error code -> document -> monitoring workflow', async ({ page, request }) => {
    // Step 1: Create document
    await dashboardPage.navigateToSection('documents');
    await documentsPage.isLoaded();

    const documentData = {
      filename: 'error-code-test.pdf',
      original_filename: 'error-code-test.pdf',
      language: 'en',
      document_type: 'service_manual',
      storage_url: 'https://example.com/error-code-test.pdf'
    };

    const documentId = await documentsPage.createDocument(documentData);

    // Step 2: Create error code linked to document
    await dashboardPage.navigateToSection('error-codes');
    await errorCodesPage.isLoaded();

    const errorCodeData = {
      error_code: 'INT001',
      error_description: 'Integration Test Error',
      severity_level: 'medium' as const,
      document_id: documentId,
      solution_steps: '1. Restart device\n2. Check connections'
    };

    await errorCodesPage.clickCreateButton();
    await errorCodesPage.fillErrorCodeForm(errorCodeData);
    const errorCodeId = await errorCodesPage.createErrorCode(errorCodeData);

    // Verify error code created
    await expect(page.locator('[data-testid="success-toast"]')).toContainText('Error code created');

    // Step 3: Check monitoring dashboard for updates
    await dashboardPage.navigateToSection('monitoring');
    await monitoringPage.isLoaded();

    // Verify monitoring data reflects new entities
    await expect(page.locator('[data-testid="metric-total-documents"]')).toBeVisible();
    await expect(page.locator('[data-testid="metric-total-error-codes"]')).toBeVisible();

    // Step 4: Test search integration
    await dashboardPage.navigateToSection('documents');
    await documentsPage.searchDocuments('error-code-test');
    
    const searchResults = await documentsPage.getRowCount();
    expect(searchResults).toBeGreaterThan(0);

    // Step 5: Clean up
    await dashboardPage.navigateToSection('error-codes');
    await errorCodesPage.navigate();
    await errorCodesPage.deleteErrorCode(0);
    await dashboardPage.navigateToSection('documents');
    await documentsPage.navigate();
    await documentsPage.deleteDocument(0);
  });

  test('should complete video -> manufacturer -> product workflow', async ({ page, request }) => {
    // Step 1: Create manufacturer
    const manufacturerId = await createTestManufacturer(request, {
      name: 'Video Test Manufacturer',
      short_name: 'VIDTEST'
    });

    // Step 2: Create product
    const productId = await createTestProduct(request, {
      model_number: 'VID-TEST-001',
      model_name: 'Video Test Product',
      manufacturer_id: manufacturerId
    });

    // Step 3: Create video linked to manufacturer
    await dashboardPage.navigateToSection('videos');
    await videosPage.isLoaded();

    const videoData = {
      title: 'Integration Test Video',
      url: 'https://youtube.com/watch?v=test123',
      platform: 'youtube' as const,
      youtube_id: 'test123',
      manufacturer_id: manufacturerId
    };

    await videosPage.clickCreateButton();
    await videosPage.fillVideoForm(videoData);
    const videoId = await videosPage.createVideo(videoData);

    // Verify video created
    await expect(page.locator('[data-testid="success-toast"]')).toContainText('Video created');

    // Step 4: Verify video appears in searches
    await videosPage.searchVideos('Integration Test Video');
    const searchResults = await videosPage.getRowCount();
    expect(searchResults).toBeGreaterThan(0);

    // Step 5: Verify relationships in product page
    await dashboardPage.navigateToSection('products');
    await productsPage.navigate();
    await productsPage.searchProducts('VID-TEST-001');
    
    const productResults = await productsPage.getRowCount();
    expect(productResults).toBeGreaterThan(0);

    // Step 6: Clean up
    await dashboardPage.navigateToSection('videos');
    await videosPage.navigate();
    await videosPage.deleteVideo(0);
    
    // Clean up created entities via API
    await request.delete(`/api/v1/products/${productId}`);
    await request.delete(`/api/v1/manufacturers/${manufacturerId}`);
  });

  test('should handle batch operations across entities', async ({ page, request }) => {
    // Create multiple test entities
    const manufacturerId = await createTestManufacturer(request);
    const productIds = [];
    const documentIds = [];

    // Create multiple products
    for (let i = 0; i < 3; i++) {
      const productId = await createTestProduct(request, {
        model_number: `BATCH-TEST-${i}`,
        manufacturer_id: manufacturerId
      });
      productIds.push(productId);
    }

    // Create multiple documents
    for (let i = 0; i < 3; i++) {
      const documentId = await createTestDocument(request, {
        filename: `batch-test-${i}.pdf`,
        product_id: productIds[i]
      });
      documentIds.push(documentId);
    }

    // Test batch delete on products
    await dashboardPage.navigateToSection('products');
    await productsPage.isLoaded();
    
    await productsPage.selectRows(3);
    await productsPage.batchDelete(3);

    // Verify batch delete completed
    await expect(page.locator('[data-testid="success-toast"]')).toContainText('Batch delete completed');

    // Test batch delete on documents
    await dashboardPage.navigateToSection('documents');
    await documentsPage.isLoaded();
    
    await documentsPage.selectRows(3);
    await documentsPage.batchDelete(3);

    // Verify batch delete completed
    await expect(page.locator('[data-testid="success-toast"]')).toContainText('Batch delete completed');

    // Clean up manufacturer
    await request.delete(`/api/v1/manufacturers/${manufacturerId}`);
  });

  test('should handle cross-entity search and filtering', async ({ page, request }) => {
    // Create related entities
    const manufacturerId = await createTestManufacturer(request, {
      name: 'Search Test Manufacturer',
      short_name: 'SEARCHTEST'
    });

    const productId = await createTestProduct(request, {
      model_number: 'SEARCH-001',
      model_name: 'Search Test Product',
      manufacturer_id: manufacturerId
    });

    const documentId = await createTestDocument(request, {
      filename: 'search-test-manual.pdf',
      product_id: productId,
      manufacturer_id: manufacturerId
    });

    const errorCodeId = await createTestErrorCode(request, {
      error_code: 'SEARCH001',
      document_id: documentId,
      manufacturer_id: manufacturerId
    });

    // Test search across different entities
    await dashboardPage.navigateToSection('documents');
    await documentsPage.searchDocuments('SEARCHTEST');
    expect(await documentsPage.getRowCount()).toBeGreaterThan(0);

    await dashboardPage.navigateToSection('products');
    await productsPage.searchProducts('SEARCH-001');
    expect(await productsPage.getRowCount()).toBeGreaterThan(0);

    await dashboardPage.navigateToSection('error-codes');
    await errorCodesPage.searchErrorCodes('SEARCH001');
    expect(await errorCodesPage.getRowCount()).toBeGreaterThan(0);

    // Test filtering by manufacturer
    await dashboardPage.navigateToSection('products');
    await productsPage.applyFilter('manufacturer_id', manufacturerId);
    expect(await productsPage.getRowCount()).toBeGreaterThan(0);

    // Clean up
    await request.delete(`/api/v1/error-codes/${errorCodeId}`);
    await request.delete(`/api/v1/documents/${documentId}`);
    await request.delete(`/api/v1/products/${productId}`);
    await request.delete(`/api/v1/manufacturers/${manufacturerId}`);
  });

  test('should handle real-time updates across multiple sessions', async ({ browser, request }) => {
    // Create two separate sessions
    const context1 = await browser.newContext();
    const context2 = await browser.newContext();
    
    const page1 = await context1.newPage();
    const page2 = await context2.newPage();

    const loginPage1 = new LoginPage(page1);
    const loginPage2 = new LoginPage(page2);
    const dashboardPage1 = new DashboardPage(page1);
    const dashboardPage2 = new DashboardPage(page2);
    const documentsPage1 = new DocumentsPage(page1);
    const documentsPage2 = new DocumentsPage(page2);

    // Login both sessions
    await loginPage1.navigate();
    await loginPage1.login('admin@example.com', 'adminpass');
    await dashboardPage1.isLoaded();

    await loginPage2.navigate();
    await loginPage2.login('editor@example.com', 'editorpass');
    await dashboardPage2.isLoaded();

    // Navigate both to documents
    await dashboardPage1.navigateToSection('documents');
    await documentsPage1.isLoaded();

    await dashboardPage2.navigateToSection('documents');
    await documentsPage2.isLoaded();

    // Create document in session 1
    const documentData = {
      filename: 'realtime-test.pdf',
      original_filename: 'realtime-test.pdf',
      language: 'en',
      document_type: 'service_manual',
      storage_url: 'https://example.com/realtime-test.pdf'
    };

    const documentId = await documentsPage1.createDocument(documentData);

    // Verify document appears in session 2 (with real-time updates if WebSocket is enabled)
    await documentsPage2.searchDocuments('realtime-test');
    
    // If real-time updates are working, it should appear immediately
    // Otherwise, manual refresh might be needed
    const initialCount = await documentsPage2.getRowCount();
    if (initialCount === 0) {
      await page2.reload();
      await documentsPage2.searchDocuments('realtime-test');
    }

    expect(await documentsPage2.getRowCount()).toBeGreaterThan(0);

    // Clean up
    await request.delete(`/api/v1/documents/${documentId}`);
    await context1.close();
    await context2.close();
  });

  test('should handle complex workflow with error recovery', async ({ page, request }) => {
    // Step 1: Create manufacturer
    const manufacturerId = await createTestManufacturer(request, {
      name: 'Complex Workflow Test',
      short_name: 'COMPLEX'
    });

    try {
      // Step 2: Create product
      const productId = await createTestProduct(request, {
        model_number: 'COMPLEX-001',
        manufacturer_id: manufacturerId
      });

      try {
        // Step 3: Create document
        const documentId = await createTestDocument(request, {
          filename: 'complex-workflow.pdf',
          product_id: productId
        });

        try {
          // Step 4: Create error code
          const errorCodeId = await createTestErrorCode(request, {
            error_code: 'COMPLEX001',
            document_id: documentId
          });

          // Verify all entities exist in UI
          await dashboardPage.navigateToSection('documents');
          await documentsPage.searchDocuments('complex-workflow');
          expect(await documentsPage.getRowCount()).toBeGreaterThan(0);

          await dashboardPage.navigateToSection('error-codes');
          await errorCodesPage.searchErrorCodes('COMPLEX001');
          expect(await errorCodesPage.getRowCount()).toBeGreaterThan(0);

          // Clean up in reverse order
          await request.delete(`/api/v1/error-codes/${errorCodeId}`);

        } catch (error) {
          console.log('Error code creation failed, cleaning up document');
          throw error;
        } finally {
          await request.delete(`/api/v1/documents/${documentId}`);
        }

      } catch (error) {
        console.log('Document creation failed, cleaning up product');
        throw error;
      } finally {
        await request.delete(`/api/v1/products/${productId}`);
      }

    } catch (error) {
      console.log('Product creation failed, cleaning up manufacturer');
      throw error;
    } finally {
      await request.delete(`/api/v1/manufacturers/${manufacturerId}`);
    }
  });
});
