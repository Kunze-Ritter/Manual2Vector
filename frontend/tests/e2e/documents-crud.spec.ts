// Playwright E2E tests for document CRUD flows
import { test, expect } from '@playwright/test';
import { LoginPage } from './page-objects/LoginPage';
import { DocumentsPage } from './page-objects/DocumentsPage';

test.describe('Documents CRUD', () => {
  let loginPage: LoginPage;
  let documentsPage: DocumentsPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    documentsPage = new DocumentsPage(page);
    
    await loginPage.navigate();
    await loginPage.loginAsAdmin();
    await documentsPage.navigate();
  });

  test('Create a new document', async ({ page }) => {
    const documentData = {
      filename: 'test-document.pdf',
      original_filename: 'test-document.pdf',
      language: 'en-US',
      document_type: 'manual',
      storage_url: 'https://example.com/test.pdf',
    };

    await documentsPage.createDocument(documentData);
    
    // Verify document was created
    const rowCount = await documentsPage.getRowCount();
    expect(rowCount).toBeGreaterThan(0);
    
    // Verify the document appears in the table
    const documentDataFromTable = await documentsPage.getDocumentData(0);
    expect(documentDataFromTable.filename).toBe(documentData.filename);
  });

  test('Edit an existing document', async ({ page }) => {
    // First create a document to edit
    const documentData = {
      filename: 'editable-document.pdf',
      original_filename: 'editable-document.pdf',
      language: 'en-US',
      document_type: 'manual',
      storage_url: 'https://example.com/editable.pdf',
    };
    
    await documentsPage.createDocument(documentData);
    
    // Edit the document
    const updatedData = {
      filename: 'edited-document.pdf',
      language: 'de-DE',
    };
    
    await documentsPage.editDocument(0, updatedData);
    
    // Verify the document was updated
    const documentDataFromTable = await documentsPage.getDocumentData(0);
    expect(documentDataFromTable.filename).toBe(updatedData.filename);
    expect(documentDataFromTable.language).toBe(updatedData.language);
  });

  test('Delete a document', async ({ page }) => {
    // First create a document to delete
    const documentData = {
      filename: 'deletable-document.pdf',
      original_filename: 'deletable-document.pdf',
      language: 'en-US',
      document_type: 'manual',
      storage_url: 'https://example.com/deletable.pdf',
    };
    
    await documentsPage.createDocument(documentData);
    const initialCount = await documentsPage.getRowCount();
    
    // Delete the document
    await documentsPage.deleteDocument(0);
    
    // Verify the document was deleted
    const finalCount = await documentsPage.getRowCount();
    expect(finalCount).toBeLessThan(initialCount);
  });

  test('Search documents', async ({ page }) => {
    // Create test documents
    const documentData1 = {
      filename: 'search-test-manual.pdf',
      original_filename: 'search-test-manual.pdf',
      language: 'en-US',
      document_type: 'manual',
      storage_url: 'https://example.com/manual.pdf',
    };
    
    const documentData2 = {
      filename: 'other-document.pdf',
      original_filename: 'other-document.pdf',
      language: 'en-US',
      document_type: 'bulletin',
      storage_url: 'https://example.com/other.pdf',
    };
    
    await documentsPage.createDocument(documentData1);
    await documentsPage.createDocument(documentData2);
    
    // Search for specific document
    const resultCount = await documentsPage.searchDocuments('search-test');
    expect(resultCount).toBe(1);
    
    // Clear search
    await documentsPage.clearSearch();
    const allCount = await documentsPage.getRowCount();
    expect(allCount).toBeGreaterThan(1);
  });

  test('Filter documents by type', async ({ page }) => {
    // Create test documents with different types
    const manualData = {
      filename: 'filter-manual.pdf',
      original_filename: 'filter-manual.pdf',
      language: 'en-US',
      document_type: 'manual',
      storage_url: 'https://example.com/manual.pdf',
    };
    
    const bulletinData = {
      filename: 'filter-bulletin.pdf',
      original_filename: 'filter-bulletin.pdf',
      language: 'en-US',
      document_type: 'bulletin',
      storage_url: 'https://example.com/bulletin.pdf',
    };
    
    await documentsPage.createDocument(manualData);
    await documentsPage.createDocument(bulletinData);
    
    // Filter by manual type
    const resultCount = await documentsPage.applyFilter('document_type', 'manual');
    expect(resultCount).toBe(1);
    
    // Reset filters
    await documentsPage.resetFilters();
    const allCount = await documentsPage.getRowCount();
    expect(allCount).toBeGreaterThan(1);
  });

  test('Sort documents by column', async ({ page }) => {
    // Create test documents with different upload times
    const documentData1 = {
      filename: 'sort-test-1.pdf',
      original_filename: 'sort-test-1.pdf',
      language: 'en-US',
      document_type: 'manual',
      storage_url: 'https://example.com/sort1.pdf',
    };
    
    const documentData2 = {
      filename: 'sort-test-2.pdf',
      original_filename: 'sort-test-2.pdf',
      language: 'en-US',
      document_type: 'manual',
      storage_url: 'https://example.com/sort2.pdf',
    };
    
    await documentsPage.createDocument(documentData1);
    await documentsPage.createDocument(documentData2);
    
    // Sort by filename ascending
    const sortOrder = await documentsPage.sortByColumn('filename');
    expect(sortOrder).toBe('asc');
    
    // Sort again to change order
    const newSortOrder = await documentsPage.sortByColumn('filename');
    expect(newSortOrder).toBe('desc');
  });

  test('Pagination navigation', async ({ page }) => {
    // Create enough documents to test pagination
    for (let i = 0; i < 25; i++) {
      const documentData = {
        filename: `pagination-test-${i}.pdf`,
        original_filename: `pagination-test-${i}.pdf`,
        language: 'en-US',
        document_type: 'manual',
        storage_url: `https://example.com/pagination-${i}.pdf`,
      };
      await documentsPage.createDocument(documentData);
    }
    
    // Get pagination info
    const paginationInfo = await documentsPage.getPaginationInfo();
    expect(paginationInfo.totalItems).toBeGreaterThan(20);
    expect(paginationInfo.totalPages).toBeGreaterThan(1);
    
    // Navigate to next page
    const nextPageCount = await documentsPage.goToNextPage();
    expect(nextPageCount).toBeGreaterThan(0);
    
    // Navigate back to previous page
    const prevPageCount = await documentsPage.goToPrevPage();
    expect(prevPageCount).toBeGreaterThan(0);
  });
});
