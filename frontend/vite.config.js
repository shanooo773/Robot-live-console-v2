import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    host: true // Allow external access for local testing
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
