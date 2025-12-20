import React, { createContext, useContext, useEffect, useState } from 'react';

type Theme = 'light' | 'dark' | 'system';

interface ThemeContextType {
  theme: Theme;
  setTheme: (theme: Theme) => void;
  actualTheme: 'light' | 'dark'; // The resolved theme (system preference resolved)
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

const STORAGE_KEY = 'krai-theme';

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setThemeState] = useState<Theme>(() => {
    // Initialize from localStorage or default to 'system'
    if (typeof window !== 'undefined' && typeof localStorage !== 'undefined') {
      const stored = localStorage.getItem(STORAGE_KEY) as Theme | null;
      return stored || 'system';
    }
    return 'system';
  });

  const [actualTheme, setActualTheme] = useState<'light' | 'dark'>(() => {
    // Determine initial actual theme
    if (typeof window !== 'undefined' && theme === 'system') {
      return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }
    return theme === 'system' ? 'light' : theme;
  });

  // Update actual theme when theme changes or system preference changes
  useEffect(() => {
    // Guard against SSR/non-DOM environments
    if (typeof window === 'undefined' || typeof document === 'undefined') {
      return;
    }

    const root = document.documentElement;
    
    const updateActualTheme = () => {
      let newActualTheme: 'light' | 'dark';
      
      if (theme === 'system') {
        newActualTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
      } else {
        newActualTheme = theme;
      }
      
      setActualTheme(newActualTheme);
      
      // Apply theme to document
      if (newActualTheme === 'dark') {
        root.classList.add('dark');
      } else {
        root.classList.remove('dark');
      }
    };

    updateActualTheme();

    // Listen for system preference changes when theme is 'system'
    if (theme === 'system') {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
      const handleChange = () => updateActualTheme();
      
      // Modern browsers
      if (mediaQuery.addEventListener) {
        mediaQuery.addEventListener('change', handleChange);
        return () => mediaQuery.removeEventListener('change', handleChange);
      } else {
        // Fallback for older browsers
        mediaQuery.addListener(handleChange);
        return () => mediaQuery.removeListener(handleChange);
      }
    }
  }, [theme]);

  const setTheme = (newTheme: Theme) => {
    setThemeState(newTheme);
    if (typeof window !== 'undefined' && typeof localStorage !== 'undefined') {
      localStorage.setItem(STORAGE_KEY, newTheme);
    }
  };

  return (
    <ThemeContext.Provider value={{ theme, setTheme, actualTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}
