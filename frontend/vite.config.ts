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
      provider: 'v8',
      reporter: ['text', 'html'],
      // Scope de cobertura a las capas con tests propios. Las páginas de
      // composición (src/pages) se testean indirectamente vía sus formularios
      // y App.test. Los wrappers de src/api son envoltorios delgados sobre
      // axios que los consumidores mockean en sus propios tests.
      include: [
        'src/components/**/*.{ts,tsx}',
        'src/hooks/**/*.{ts,tsx}',
        'src/lib/**/*.{ts,tsx}',
        'src/stores/**/*.{ts,tsx}',
      ],
      exclude: [
        'src/**/*.test.{ts,tsx}',
      ],
      thresholds: {
        lines: 70,
        functions: 70,
        branches: 70,
        statements: 70,
      },
    },
  },
});
