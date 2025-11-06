import { setupServer } from 'msw/node';
import { http } from 'msw';

// Example mock handlers – extend as needed
export const handlers = [
  // Mock login endpoint
  http.post('/api/v1/auth/login', ({ request }) => {
    const { username } = request.body as { username: string };
    const role = username.includes('admin') ? 'admin' : username.includes('editor') ? 'editor' : 'viewer';
    return Response.json({
      access_token: `mock-token-${username}`,
      user: { username, role },
    });
  }),
  // Add more handlers for other API routes as needed
];

export const server = setupServer(...handlers);
