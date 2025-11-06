/**
 * Authentication utilities for the KRAI application
 */

/**
 * Get the current access token from localStorage
 * @returns The access token or null if not found/expired
 */
export function getAccessToken(): string | null {
  try {
    const token = localStorage.getItem('access_token');
    if (!token) return null;
    
    // Optional: Add token expiration check here if needed
    // const payload = JSON.parse(atob(token.split('.')[1]));
    // if (payload.exp * 1000 < Date.now()) {
    //   localStorage.removeItem('access_token');
    //   return null;
    // }
    
    return token;
  } catch (error) {
    console.error('Error getting access token:', error);
    return null;
  }
}

/**
 * Set the access token in localStorage
 * @param token The JWT access token
 */
export function setAccessToken(token: string): void {
  try {
    localStorage.setItem('access_token', token);
  } catch (error) {
    console.error('Error setting access token:', error);
  }
}

/**
 * Remove the access token from localStorage
 */
export function removeAccessToken(): void {
  try {
    localStorage.removeItem('access_token');
  } catch (error) {
    console.error('Error removing access token:', error);
  }
}

/**
 * Check if the user is authenticated
 * @returns boolean indicating if the user is authenticated
 */
export function isAuthenticated(): boolean {
  return !!getAccessToken();
}

export default {
  getAccessToken,
  setAccessToken,
  removeAccessToken,
  isAuthenticated,
};
