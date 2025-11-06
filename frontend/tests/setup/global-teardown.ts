import axios from 'axios';
import type { FullConfig } from '@playwright/test';
import { readFileSync, existsSync, unlinkSync } from 'fs';
import { join } from 'path';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

async function globalTeardown(_config: FullConfig) {
  console.log('🧹 Starting global teardown...');
  
  const apiURL = process.env.API_URL || 'http://localhost:8000';
  const cleanupUsers = process.env.CLEANUP_TEST_USERS === 'true';
  
  // Load test state
  const stateFile = join(__dirname, 'test-state.json');
  
  let testState: any = {};
  try {
    if (existsSync(stateFile)) {
      testState = JSON.parse(readFileSync(stateFile, 'utf8'));
      console.log('📖 Loaded test state from file');
    }
  } catch (error) {
    console.error('⚠️  Failed to load test state:', error);
  }

  // Cleanup created entities
  const cleanupStats = { usersDeleted: 0, entitiesDeleted: 0, errors: [] as string[] };

  // Cleanup test manufacturer if created
  if (testState.manufacturer?.id) {
    try {
      const adminUser = testState.users.find((u: any) => u.role === 'admin') || testState.users[0];
      if (adminUser) {
        const token = await getAuthToken(adminUser.email, adminUser.password, apiURL);
        
        await axios.delete(`${apiURL}/api/v1/manufacturers/${testState.manufacturer.id}`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        });
        
        cleanupStats.entitiesDeleted++;
        console.log(`🗑️  Deleted test manufacturer: ${testState.manufacturer.id}`);
      }
    } catch (error: any) {
      console.error('❌ Failed to delete test manufacturer:', error.response?.data?.message || error.message);
      cleanupStats.errors.push(`Manufacturer: ${error.message}`);
    }
  }

  // Cleanup test users if requested
  if (cleanupUsers && testState.users) {
    console.log('🗑️  Cleaning up test users...');
    
    for (const user of testState.users) {
      if (user.exists) {
        console.log(`⏭️  Skipping existing user: ${user.email}`);
        continue;
      }
      
      try {
        // Use admin user to delete other users
        const adminUser = testState.users.find((u: any) => u.role === 'admin') || testState.users[0];
        if (adminUser && adminUser.email !== user.email) {
          const token = await getAuthToken(adminUser.email, adminUser.password, apiURL);
          
          await axios.delete(`${apiURL}/api/v1/users/${user.id}`, {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json',
            },
          });
          
          cleanupStats.usersDeleted++;
          console.log(`🗑️  Deleted user: ${user.email}`);
        }
      } catch (error: any) {
        console.error(`❌ Failed to delete user ${user.email}:`, error.response?.data?.message || error.message);
        cleanupStats.errors.push(`User ${user.email}: ${error.message}`);
      }
    }
  }

  // Remove state file
  try {
    if (existsSync(stateFile)) {
      unlinkSync(stateFile);
      console.log('🗑️  Removed test state file');
    }
  } catch (error) {
    console.error('⚠️  Failed to remove test state file:', error);
  }

  // Print summary
  console.log('\n📊 Teardown Summary:');
  console.log(`  Users deleted: ${cleanupStats.usersDeleted}`);
  console.log(`  Entities deleted: ${cleanupStats.entitiesDeleted}`);
  if (cleanupStats.errors.length > 0) {
    console.log(`  Errors: ${cleanupStats.errors.length}`);
    cleanupStats.errors.forEach((error: string) => console.log(`    - ${error}`));
  }
  
  console.log('✅ Global teardown completed');
}

async function getAuthToken(email: string, password: string, apiURL: string): Promise<string> {
  const response = await axios.post(`${apiURL}/api/v1/auth/login`, {
    email,
    password,
  });
  
  if (response.data.success && response.data.data?.token) {
    return response.data.data.token;
  }
  
  throw new Error('Failed to get auth token');
}

export default globalTeardown;
