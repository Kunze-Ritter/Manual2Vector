import { APIRequestContext } from '@playwright/test';
import { DocumentFormData, ProductFormData, ManufacturerFormData, ErrorCodeFormData, VideoFormData } from '../page-objects';

// Environment variables for test configuration
const TEST_CONFIG = {
  API_URL: 'http://localhost:8000',
  ADMIN_USERNAME: 'admin@example.com',
  ADMIN_PASSWORD: 'adminpass',
  EDITOR_USERNAME: 'editor@example.com',
  EDITOR_PASSWORD: 'editorpass',
  VIEWER_USERNAME: 'viewer@example.com',
  VIEWER_PASSWORD: 'viewerpass'
} as const;

// Global test data tracking
let testDocumentIds: string[] = [];
let testProductIds: string[] = [];
let testManufacturerIds: string[] = [];
let testErrorCodeIds: string[] = [];
let testVideoIds: string[] = [];

/**
 * Setup test users via API if they don't exist
 */
export async function setupTestUsers(request: APIRequestContext): Promise<void> {
  const baseURL = TEST_CONFIG.API_URL;
  
  const users = [
    {
      email: TEST_CONFIG.ADMIN_USERNAME,
      password: TEST_CONFIG.ADMIN_PASSWORD,
      role: 'admin'
    },
    {
      email: TEST_CONFIG.EDITOR_USERNAME,
      password: TEST_CONFIG.EDITOR_PASSWORD,
      role: 'editor'
    },
    {
      email: TEST_CONFIG.VIEWER_USERNAME,
      password: TEST_CONFIG.VIEWER_PASSWORD,
      role: 'viewer'
    }
  ];

  for (const user of users) {
    try {
      // Try to register user
      const response = await request.post(`${baseURL}/api/v1/auth/register`, {
        data: user
      });
      
      if (response.status() === 409) {
        // User already exists, that's fine
        console.log(`User ${user.email} already exists`);
      } else if (!response.ok()) {
        console.warn(`Failed to create user ${user.email}: ${response.status()}`);
      }
    } catch (error) {
      console.warn(`Error creating user ${user.email}:`, error);
    }
  }
}

/**
 * Get auth token for API requests
 */
export async function getAuthToken(request: APIRequestContext, email: string, password: string): Promise<string> {
  const baseURL = TEST_CONFIG.API_URL;
  
  const response = await request.post(`${baseURL}/api/v1/auth/login`, {
    data: { email, password }
  });
  
  if (!response.ok()) {
    throw new Error(`Failed to get auth token: ${response.status()}`);
  }
  
  const data = await response.json();
  return data.access_token;
}

/**
 * Make authenticated API request
 */
export async function makeAuthenticatedRequest(
  request: APIRequestContext,
  method: string,
  url: string,
  data?: any,
  token?: string
): Promise<any> {
  const baseURL = TEST_CONFIG.API_URL;
  const fullUrl = url.startsWith('http') ? url : `${baseURL}${url}`;
  
  const headers = {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  };
  
  let response;
  switch (method.toUpperCase()) {
    case 'GET':
      response = await request.get(fullUrl, { headers });
      break;
    case 'POST':
      response = await request.post(fullUrl, { headers, data });
      break;
    case 'PUT':
      response = await request.put(fullUrl, { headers, data });
      break;
    case 'DELETE':
      response = await request.delete(fullUrl, { headers });
      break;
    default:
      throw new Error(`Unsupported method: ${method}`);
  }
  
  if (!response.ok()) {
    throw new Error(`API request failed: ${response.status()} ${response.statusText()}`);
  }
  
  return response.json();
}

/**
 * Create test document via API
 */
export async function createTestDocument(
  request: APIRequestContext,
  data?: Partial<DocumentFormData>
): Promise<string> {
  const defaultData: DocumentFormData = {
    filename: `test-document-${Date.now()}.pdf`,
    original_filename: `test-document-${Date.now()}.pdf`,
    language: 'en',
    document_type: 'service_manual',
    storage_url: `https://example.com/test-document-${Date.now()}.pdf`,
    processing_status: 'completed',
    manual_review_required: false
  };
  
  const documentData = { ...defaultData, ...data };
  const token = await getAuthToken(request, 
    TEST_CONFIG.ADMIN_USERNAME,
    TEST_CONFIG.ADMIN_PASSWORD
  );
  
  const response = await makeAuthenticatedRequest(
    request,
    'POST',
    '/api/v1/documents',
    documentData,
    token
  );
  
  const documentId = response.data?.id || response.id;
  testDocumentIds.push(documentId);
  
  return documentId;
}

/**
 * Create test product via API
 */
export async function createTestProduct(
  request: APIRequestContext,
  data?: Partial<ProductFormData>
): Promise<string> {
  const defaultData: ProductFormData = {
    model_number: `TEST-${Date.now()}`,
    model_name: `Test Product ${Date.now()}`,
    product_type: 'printer',
    manufacturer_id: '', // Will be set dynamically
    network_capable: true,
    print_technology: 'laser'
  };
  
  let productData = { ...defaultData, ...data };
  
  // If no manufacturer_id provided, create one or get first available
  if (!productData.manufacturer_id) {
    if (data?.manufacturer_id) {
      productData.manufacturer_id = data.manufacturer_id;
    } else {
      // Create a test manufacturer first
      const manufacturerId = await createTestManufacturer(request);
      productData.manufacturer_id = manufacturerId;
    }
  }
  
  const token = await getAuthToken(request, 
    TEST_CONFIG.ADMIN_USERNAME,
    TEST_CONFIG.ADMIN_PASSWORD
  );
  
  const response = await makeAuthenticatedRequest(
    request,
    'POST',
    '/api/v1/products',
    productData,
    token
  );
  
  const productId = response.data?.id || response.id;
  testProductIds.push(productId);
  
  return productId;
}

/**
 * Create test manufacturer via API
 */
export async function createTestManufacturer(
  request: APIRequestContext,
  data?: Partial<ManufacturerFormData>
): Promise<string> {
  const defaultData: ManufacturerFormData = {
    name: `Test Manufacturer ${Date.now()}`,
    short_name: `TEST${Date.now()}`,
    country: 'USA',
    founded_year: 2020,
    website: `https://test-${Date.now()}.com`,
    support_email: `support@test-${Date.now()}.com`,
    is_competitor: false,
    market_share_percent: 1.0,
    employee_count: 100
  };
  
  const manufacturerData = { ...defaultData, ...data };
  const token = await getAuthToken(request,
    TEST_CONFIG.ADMIN_USERNAME,
    TEST_CONFIG.ADMIN_PASSWORD
  );
  
  const response = await makeAuthenticatedRequest(
    request,
    'POST',
    '/api/v1/manufacturers',
    manufacturerData,
    token
  );
  
  const manufacturerId = response.data?.id || response.id;
  testManufacturerIds.push(manufacturerId);
  
  return manufacturerId;
}

/**
 * Create test error code via API
 */
export async function createTestErrorCode(
  request: APIRequestContext,
  data?: Partial<ErrorCodeFormData>
): Promise<string> {
  const defaultData: ErrorCodeFormData = {
    error_code: `TEST${Date.now()}`,
    error_description: `Test error code ${Date.now()}`,
    severity_level: 'medium',
    requires_technician: false,
    requires_parts: false,
    estimated_fix_time_minutes: 30,
    solution_steps: '1. Restart device\n2. Check connections\n3. Contact support if issue persists'
  };
  
  const errorCodeData = { ...defaultData, ...data };
  const token = await getAuthToken(request, 
    TEST_CONFIG.ADMIN_USERNAME,
    TEST_CONFIG.ADMIN_PASSWORD
  );
  
  const response = await makeAuthenticatedRequest(
    request,
    'POST',
    '/api/v1/error-codes',
    errorCodeData,
    token
  );
  
  const errorCodeId = response.data?.id || response.id;
  testErrorCodeIds.push(errorCodeId);
  
  return errorCodeId;
}

/**
 * Create test video via API
 */
export async function createTestVideo(
  request: APIRequestContext,
  data?: Partial<VideoFormData>
): Promise<string> {
  const defaultData: VideoFormData = {
    title: `Test Video ${Date.now()}`,
    url: `https://youtube.com/watch?v=test${Date.now()}`,
    platform: 'youtube',
    youtube_id: `test${Date.now()}`,
    duration_seconds: 300,
    view_count: 1000,
    thumbnail_url: `https://img.youtube.com/vi/test${Date.now()}/maxresdefault.jpg`
  };
  
  const videoData = { ...defaultData, ...data };
  const token = await getAuthToken(request, 
    TEST_CONFIG.ADMIN_USERNAME,
    TEST_CONFIG.ADMIN_PASSWORD
  );
  
  const response = await makeAuthenticatedRequest(
    request,
    'POST',
    '/api/v1/videos',
    videoData,
    token
  );
  
  const videoId = response.data?.id || response.id;
  testVideoIds.push(videoId);
  
  return videoId;
}

/**
      token
    );
  } catch (error) {
    console.warn(`Failed to batch delete entities from ${endpoint}:`, error);
    // Fallback to individual deletion
    for (const id of ids) {
      await deleteEntity(request, endpoint, id);
    }
  }
}

/**
 * Cleanup test data created during tests
 */
export async function cleanupTestData(request: APIRequestContext): Promise<void> {
  console.log('Cleaning up test data...');
  
  // Delete in reverse order of dependencies
  await batchDeleteEntities(request, '/api/v1/videos', testVideoIds);
  await batchDeleteEntities(request, '/api/v1/error-codes', testErrorCodeIds);
  await batchDeleteEntities(request, '/api/v1/documents', testDocumentIds);
  await batchDeleteEntities(request, '/api/v1/products', testProductIds);
  await batchDeleteEntities(request, '/api/v1/manufacturers', testManufacturerIds);
  
  // Clear tracking arrays
  testDocumentIds = [];
  testProductIds = [];
  testManufacturerIds = [];
  testErrorCodeIds = [];
  testVideoIds = [];
  
  console.log('Test data cleanup completed');
}

/**
 * Get tracked test entity IDs
 */
export function getTrackedEntityIds(): {
  documents: string[];
  products: string[];
  manufacturers: string[];
  errorCodes: string[];
  videos: string[];
} {
  return {
    documents: [...testDocumentIds],
    products: [...testProductIds],
    manufacturers: [...testManufacturerIds],
    errorCodes: [...testErrorCodeIds],
    videos: [...testVideoIds]
  };
}

/**
 * Create multiple test entities for bulk testing
 */
export async function createBulkTestData(request: APIRequestContext, count: number = 5): Promise<void> {
  console.log(`Creating ${count} test entities of each type...`);
  
  for (let i = 0; i < count; i++) {
    await createTestDocument(request);
    await createTestProduct(request);
    await createTestManufacturer(request);
    await createTestErrorCode(request);
    await createTestVideo(request);
  }
  
  console.log('Bulk test data creation completed');
}

/**
 * Seed test data for integration tests
 */
export async function seedIntegrationTestData(request: APIRequestContext): Promise<{
  manufacturerId: string;
  productId: string;
  documentId: string;
  errorCodeId: string;
  videoId: string;
}> {
  // Create manufacturer first
  const manufacturerId = await createTestManufacturer(request, {
    name: 'Integration Test Manufacturer',
    short_name: 'INTTEST'
  });
  
  // Create product linked to manufacturer
  const productId = await createTestProduct(request, {
    model_number: 'INT-TEST-001',
    model_name: 'Integration Test Product',
    manufacturer_id: manufacturerId
  });
  
  // Create document linked to product
  const documentId = await createTestDocument(request, {
    filename: 'integration-test-manual.pdf',
    product_id: productId,
    manufacturer_id: manufacturerId
  });
  
  // Create error code linked to document and manufacturer
  const errorCodeId = await createTestErrorCode(request, {
    error_code: 'INT001',
    document_id: documentId,
    manufacturer_id: manufacturerId
  });
  
  // Create video linked to manufacturer
  const videoId = await createTestVideo(request, {
    title: 'Integration Test Video',
    manufacturer_id: manufacturerId
  });
  
  return {
    manufacturerId,
    productId,
    documentId,
    errorCodeId,
    videoId
  };
}
