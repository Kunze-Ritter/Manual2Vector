import path from 'node:path'

import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
// 
// Environment Variables:
// - Vite automatically loads .env.production when NODE_ENV=production
// - Variables prefixed with VITE_ are exposed to the client code
// - These are baked into the build at compile time, not available at runtime
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    // Development proxy - forwards /api requests to backend
    // In production, nginx handles this (see nginx/nginx-simple.conf)
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    // Source maps for error tracking (consider 'hidden' for production)
    sourcemap: true,
    // Faster minification with esbuild
    minify: 'esbuild',
    // CSS code splitting for better loading performance
    cssCodeSplit: true,
    // Increase chunk size warning limit to avoid warnings for larger chunks
    chunkSizeWarningLimit: 1000,
    // Rollup options for better code splitting
    rollupOptions: {
      output: {
        manualChunks: {
          // Separate vendor chunks for better caching
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          'ui-vendor': ['@radix-ui/react-dialog', '@radix-ui/react-dropdown-menu', '@radix-ui/react-select'],
          'query-vendor': ['@tanstack/react-query', '@tanstack/react-query-devtools'],
        },
      },
    },
  },
})
