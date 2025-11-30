import type { FullConfig } from '@playwright/test';
import axios from 'axios';
import { writeFileSync } from 'fs';
import { join } from 'path';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

async function globalSetup(_config: FullConfig) {
  console.log('🚀 Starting global setup...');
  
  const baseURL = process.env.BASE_URL || 'http://localhost:3000';
  const apiURL = process.env.API_URL || 'http://localhost:8000';
  
  // Health checks
  console.log('🔍 Checking backend health...');
  try {
    const healthResponse = await axios.get(`${apiURL}/health`, { timeout: 10000 });
    if (healthResponse.status !== 200) {
      throw new Error(`Backend health check failed: ${healthResponse.status}`);
    }
    console.log('✅ Backend is healthy');
  } catch (error) {
    console.error('❌ Backend health check failed:', error);
    console.error('💡 Make sure the backend is running: docker-compose up -d');
    process.exit(1);
  }

  console.log('🔍 Checking frontend availability...');
  try {
    const frontendResponse = await axios.get(baseURL, { timeout: 10000 });
    if (frontendResponse.status !== 200) {
      throw new Error(`Frontend health check failed: ${frontendResponse.status}`);
    }
    console.log('✅ Frontend is available');
  } catch (error) {
    console.error('❌ Frontend health check failed:', error);
    console.error('💡 Make sure the frontend is running: npm run dev');
    process.exit(1);
  }

  // Create test users
  console.log('👥 Creating test users...');
  const TEST_USER_PASSWORD = 'TestUser1234!';
  const testUsers = [
    { email: 'admin@test.com', password: TEST_USER_PASSWORD, role: 'admin' },
    { email: 'editor@test.com', password: TEST_USER_PASSWORD, role: 'editor' },
    { email: 'viewer@test.com', password: TEST_USER_PASSWORD, role: 'viewer' },
  ];

  const createdEntities: any = { users: [] };

  for (const user of testUsers) {
    try {
      // Check if user already exists (login accepts username or email via "username" field)
      try {
        await axios.post(`${apiURL}/api/v1/auth/login`, {
          username: user.email,
          password: user.password,
        });
        console.log(`ℹ️  User ${user.email} already exists`);
        createdEntities.users.push({ ...user, exists: true });
      } catch (loginError: any) {
        if (loginError.response?.status === 401) {
          // User doesn't exist, create it (UserCreate-compatible payload)
          const username = user.email.split('@')[0];
          const registerResponse = await axios.post(`${apiURL}/api/v1/auth/register`, {
            email: user.email,
            username,
            password: user.password,
            confirm_password: user.password,
            first_name: username,
            last_name: 'Test',
          });
          
          if (registerResponse.data.success) {
            console.log(`✅ Created user: ${user.email}`);
            createdEntities.users.push({ ...user, id: registerResponse.data.data?.id, exists: false });
          } else {
            throw new Error(`Failed to create user ${user.email}: ${registerResponse.data.message}`);
          }
        } else {
          throw loginError;
        }
      }
    } catch (error: any) {
      console.error(`❌ Failed to setup user ${user.email}:`, error.response?.data || error.message);
      // Continue with other users, don't exit
    }
  }

  // Optionally seed minimal data
  console.log('🌱 Seeding minimal test data...');
  try {
    // Create a test manufacturer if needed
    const manufacturerResponse = await axios.post(
      `${apiURL}/api/v1/manufacturers`,
      { name: 'Test Manufacturer', code: 'TEST-MANU' },
      {
        headers: {
          'Authorization': `Bearer ${await getAuthToken(testUsers[0].email, testUsers[0].password, apiURL)}`,
          'Content-Type': 'application/json',
        },
      }
    );
    
    if (manufacturerResponse.data.success) {
      createdEntities.manufacturer = manufacturerResponse.data.data;
      console.log('✅ Created test manufacturer');
    }
  } catch (error: any) {
    console.log('ℹ️  Test manufacturer may already exist or failed to create:', error.response?.data?.message || error.message);
  }

  // Save state for teardown
  const stateFile = join(__dirname, 'test-state.json');
  
  try {
    writeFileSync(stateFile, JSON.stringify(createdEntities, null, 2));
    console.log('💾 Saved test state for teardown');
  } catch (error) {
    console.error('⚠️  Failed to save test state:', error);
  }

  console.log('✅ Global setup completed');
}

async function getAuthToken(email: string, password: string, apiURL: string): Promise<string> {
  const response = await axios.post(`${apiURL}/api/v1/auth/login`, {
    username: email,
    password,
  });
  
  if (response.data.success && response.data.data?.access_token) {
    return response.data.data.access_token;
  }
  
  throw new Error('Failed to get auth token');
}

export default globalSetup;
