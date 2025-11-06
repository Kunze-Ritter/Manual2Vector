// Playwright E2E tests for RBAC permission flows
import { test, expect } from '@playwright/test';
import { LoginPage } from './page-objects/LoginPage';
import { DocumentsPage } from './page-objects/DocumentsPage';
import { ProductsPage } from './page-objects/ProductsPage';

const loginAsAdmin = async (page: any) => {
  const loginPage = new LoginPage(page);
  await loginPage.navigate();
  await loginPage.login('admin@test.com', 'test123456');
};

const loginAsEditor = async (page: any) => {
  const loginPage = new LoginPage(page);
  await loginPage.navigate();
  await loginPage.login('editor@test.com', 'test123456');
};

const loginAsViewer = async (page: any) => {
  const loginPage = new LoginPage(page);
  await loginPage.navigate();
  await loginPage.login('viewer@test.com', 'test123456');
};

test.describe('Permissions', () => {
  test('Editor can create document but not delete', async ({ page }) => {
    await loginAsEditor(page);
    const documentsPage = new DocumentsPage(page);
    await documentsPage.navigate();
    
    // Editor should see create button
    const canCreate = await documentsPage.isCreateButtonVisible();
    expect(canCreate).toBe(true);
    
    // Create a document
    const documentData = {
      filename: 'editor-document.pdf',
      original_filename: 'editor-document.pdf',
      language: 'en-US',
      document_type: 'manual',
      storage_url: 'https://example.com/editor.pdf',
    };
    
    await documentsPage.createDocument(documentData);
    
    // Verify document was created
    const rowCount = await documentsPage.getRowCount();
    expect(rowCount).toBeGreaterThan(0);
    
    // Check action menu items - delete should not be available
    const actionItems = await documentsPage.getActionMenuItems(0);
    expect(actionItems).toContain('Edit');
    expect(actionItems).not.toContain('Delete');
  });

  test('Viewer can only read documents', async ({ page }) => {
    await loginAsViewer(page);
    const documentsPage = new DocumentsPage(page);
    await documentsPage.navigate();
    
    // Viewer should not see create button
    const canCreate = await documentsPage.isCreateButtonVisible();
    expect(canCreate).toBe(false);
    
    // Documents should be visible (read access)
    const isLoaded = await documentsPage.isLoaded();
    expect(isLoaded).toBe(true);
    
    // Check action menu items - should be empty or only view actions
    const actionItems = await documentsPage.getActionMenuItems(0);
    expect(actionItems).not.toContain('Edit');
    expect(actionItems).not.toContain('Delete');
  });

  test('Admin has full access to documents', async ({ page }) => {
    await loginAsAdmin(page);
    const documentsPage = new DocumentsPage(page);
    await documentsPage.navigate();
    
    // Admin should see create button
    const canCreate = await documentsPage.isCreateButtonVisible();
    expect(canCreate).toBe(true);
    
    // Check action menu items - should have all actions
    const actionItems = await documentsPage.getActionMenuItems(0);
    expect(actionItems).toContain('Edit');
    expect(actionItems).toContain('Delete');
  });

  test('Editor permissions on products', async ({ page }) => {
    await loginAsEditor(page);
    const productsPage = new ProductsPage(page);
    await productsPage.navigate();
    
    // Editor should see create button for products
    const canCreate = await productsPage.isCreateButtonVisible();
    expect(canCreate).toBe(true);
    
    // Check action menu items - should have edit but not delete
    const actionItems = await productsPage.getActionMenuItems(0);
    expect(actionItems).toContain('Edit');
    expect(actionItems).not.toContain('Delete');
  });

  test('Viewer permissions on products', async ({ page }) => {
    await loginAsViewer(page);
    const productsPage = new ProductsPage(page);
    await productsPage.navigate();
    
    // Viewer should not see create button
    const canCreate = await productsPage.isCreateButtonVisible();
    expect(canCreate).toBe(false);
    
    // Products should be visible (read access)
    const isLoaded = await productsPage.isLoaded();
    expect(isLoaded).toBe(true);
    
    // Check action menu items - should be empty
    const actionItems = await productsPage.getActionMenuItems(0);
    expect(actionItems).not.toContain('Edit');
    expect(actionItems).not.toContain('Delete');
  });

  test('API 403 responses for unauthorized actions', async ({ page }) => {
    await loginAsViewer(page);
    
    // Try to access delete API endpoint directly
    const response = await page.request.delete('/api/v1/documents/test-id', {
      headers: {
        'Authorization': `Bearer ${await page.evaluate(() => localStorage.getItem('token'))}`,
      },
    });
    
    expect(response.status()).toBe(403);
    
    const errorData = await response.json();
    expect(errorData.success).toBe(false);
    expect(errorData.message).toContain('Forbidden');
  });
});
