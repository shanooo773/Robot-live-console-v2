import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    host: true, // Allow external access for local testing
    proxy: {
      // Proxy API calls to backend during development
      '/theia': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      },
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      },
      // Add other API endpoints as needed
      '/auth': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      },
      '/bookings': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      },
      '/robots': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      },
      '/robot': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      },
      '/health': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      },
      '/announcements': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      }
    }
  },
  build: {
    // Production optimizations
    minify: 'esbuild',
    sourcemap: false, // Disable source maps for production
    rollupOptions: {
      output: {
        manualChunks: {
          // Split vendor libraries into separate chunks
          vendor: ['react', 'react-dom'],
          ui: ['@chakra-ui/react', '@emotion/react', '@emotion/styled'],
          monaco: ['@monaco-editor/react']
        }
      }
    },
    chunkSizeWarningLimit: 1000 // Increase warning limit to 1MB
  },
  define: {
    // Define global constants for production
    __DEV__: process.env.NODE_ENV !== 'production'
  }
})
