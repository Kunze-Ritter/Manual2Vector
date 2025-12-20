/**
 * Theme Utilities
 * 
 * Helper functions for theme-aware styling and testing
 */

/**
 * Get the current theme from the document
 */
export function getCurrentTheme(): 'light' | 'dark' {
  if (typeof document === 'undefined') {
    return 'light';
  }
  return document.documentElement.classList.contains('dark') ? 'dark' : 'light'
}

/**
 * Check if dark mode is active
 */
export function isDarkMode(): boolean {
  return getCurrentTheme() === 'dark'
}

/**
 * Check if light mode is active
 */
export function isLightMode(): boolean {
  return getCurrentTheme() === 'light'
}

/**
 * Get system color scheme preference
 */
export function getSystemTheme(): 'light' | 'dark' {
  if (typeof window === 'undefined') {
    return 'light';
  }
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

/**
 * Listen for system theme changes
 */
export function onSystemThemeChange(callback: (theme: 'light' | 'dark') => void): () => void {
  if (typeof window === 'undefined') {
    return () => {}; // Return no-op cleanup function
  }
  
  const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
  
  const handler = (e: MediaQueryListEvent | MediaQueryList) => {
    callback(e.matches ? 'dark' : 'light')
  }
  
  // Modern browsers
  if (mediaQuery.addEventListener) {
    mediaQuery.addEventListener('change', handler)
    return () => mediaQuery.removeEventListener('change', handler)
  } else {
    // Fallback for older browsers
    mediaQuery.addListener(handler)
    return () => mediaQuery.removeListener(handler)
  }
}

/**
 * Apply theme to document (for testing)
 */
export function applyTheme(theme: 'light' | 'dark'): void {
  if (typeof document === 'undefined') {
    return; // No-op in non-DOM environments
  }
  
  if (theme === 'dark') {
    document.documentElement.classList.add('dark')
  } else {
    document.documentElement.classList.remove('dark')
  }
}

/**
 * Get theme-aware class name
 * Useful for conditional styling based on theme
 */
export function themeClass(lightClass: string, darkClass: string): string {
  return isDarkMode() ? darkClass : lightClass
}

/**
 * Test helper: Render component in both themes
 * For use in component tests
 */
export function withThemes<T>(
  testFn: (theme: 'light' | 'dark') => T
): { light: T; dark: T } {
  const originalTheme = getCurrentTheme()
  
  applyTheme('light')
  const lightResult = testFn('light')
  
  applyTheme('dark')
  const darkResult = testFn('dark')
  
  // Restore original theme
  applyTheme(originalTheme)
  
  return { light: lightResult, dark: darkResult }
}
