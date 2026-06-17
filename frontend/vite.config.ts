import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// El proxy aplica al dev server: las llamadas a /api/* van al backend
// vía la red de docker-compose (host: backend) o localhost en local.
const BACKEND_TARGET = process.env.VITE_BACKEND_PROXY ?? 'http://backend:8000';

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    strictPort: true,
    watch: { usePolling: true },
    proxy: {
      '/api': {
        target: BACKEND_TARGET,
        changeOrigin: true,
      },
    },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/setupTests.ts',
    coverage: {
      reporter: ['text', 'html'],
    },
  },
});
