// Playwright E2E tests for product CRUD flows
import { test, expect } from '@playwright/test';
import { LoginPage } from './page-objects/LoginPage';
import { ProductsPage } from './page-objects/ProductsPage';

test.describe('Products CRUD', () => {
  let loginPage: LoginPage;
  let productsPage: ProductsPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    productsPage = new ProductsPage(page);
    
    await loginPage.navigate();
    await loginPage.loginAsAdmin();
    await productsPage.navigate();
  });

  test('Create a new product', async ({ page }) => {
    const productData = {
      model_number: 'TEST-001',
      model_name: 'Test Product',
      product_type: 'printer',
      manufacturer_id: 'test-manufacturer-id',
    };

    await productsPage.createProduct(productData);
    
    // Verify product was created
    const rowCount = await productsPage.getRowCount();
    expect(rowCount).toBeGreaterThan(0);
    
    // Verify the product appears in the table
    const productDataFromTable = await productsPage.getProductData(0);
    expect(productDataFromTable.model_name).toBe(productData.model_name);
  });

  test('Edit an existing product', async ({ page }) => {
    // First create a product to edit
    const productData = {
      model_number: 'EDIT-001',
      model_name: 'Editable Product',
      product_type: 'printer',
      manufacturer_id: 'test-manufacturer-id',
    };
    
    await productsPage.createProduct(productData);
    
    // Edit the product
    const updatedData = {
      model_name: 'Edited Product',
      product_type: 'scanner',
    };
    
    await productsPage.editProduct(0, updatedData);
    
    // Verify the product was updated
    const productDataFromTable = await productsPage.getProductData(0);
    expect(productDataFromTable.model_name).toBe(updatedData.model_name);
    expect(productDataFromTable.product_type).toBe(updatedData.product_type);
  });

  test('Delete a product', async ({ page }) => {
    // First create a product to delete
    const productData = {
      model_number: 'DEL-001',
      model_name: 'Deletable Product',
      product_type: 'printer',
      manufacturer_id: 'test-manufacturer-id',
    };
    
    await productsPage.createProduct(productData);
    const initialCount = await productsPage.getRowCount();
    
    // Delete the product
    await productsPage.deleteProduct(0);
    
    // Verify the product was deleted
    const finalCount = await productsPage.getRowCount();
    expect(finalCount).toBeLessThan(initialCount);
  });

  test('Search products', async ({ page }) => {
    // Create test products
    const productData1 = {
      model_number: 'SEARCH-001',
      model_name: 'Search Test Printer',
      product_type: 'printer',
      manufacturer_id: 'test-manufacturer-id',
    };
    
    const productData2 = {
      model_number: 'OTHER-001',
      model_name: 'Other Product',
      product_type: 'scanner',
      manufacturer_id: 'test-manufacturer-id',
    };
    
    await productsPage.createProduct(productData1);
    await productsPage.createProduct(productData2);
    
    // Search for specific product
    const resultCount = await productsPage.searchProducts('Search Test');
    expect(resultCount).toBe(1);
    
    // Clear search
    await productsPage.clearSearch();
    const allCount = await productsPage.getRowCount();
    expect(allCount).toBeGreaterThan(1);
  });

  test('Filter products by type', async ({ page }) => {
    // Create test products with different types
    const printerData = {
      model_number: 'FILTER-P-001',
      model_name: 'Filter Test Printer',
      product_type: 'printer',
      manufacturer_id: 'test-manufacturer-id',
    };
    
    const scannerData = {
      model_number: 'FILTER-S-001',
      model_name: 'Filter Test Scanner',
      product_type: 'scanner',
      manufacturer_id: 'test-manufacturer-id',
    };
    
    await productsPage.createProduct(printerData);
    await productsPage.createProduct(scannerData);
    
    // Filter by printer type
    const resultCount = await productsPage.applyFilter('product_type', 'printer');
    expect(resultCount).toBe(1);
    
    // Reset filters
    await productsPage.resetFilters();
    const allCount = await productsPage.getRowCount();
    expect(allCount).toBeGreaterThan(1);
  });

  test('Sort products by column', async ({ page }) => {
    // Create test products
    const productData1 = {
      model_number: 'SORT-001',
      model_name: 'A Product',
      product_type: 'printer',
      manufacturer_id: 'test-manufacturer-id',
    };
    
    const productData2 = {
      model_number: 'SORT-002',
      model_name: 'B Product',
      product_type: 'printer',
      manufacturer_id: 'test-manufacturer-id',
    };
    
    await productsPage.createProduct(productData1);
    await productsPage.createProduct(productData2);
    
    // Sort by name ascending
    const sortOrder = await productsPage.sortByColumn('model_name');
    expect(sortOrder).toBe('asc');
    
    // Sort again to change order
    const newSortOrder = await productsPage.sortByColumn('model_name');
    expect(newSortOrder).toBe('desc');
  });
});
