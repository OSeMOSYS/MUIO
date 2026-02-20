import { defineConfig } from 'vite';

export default defineConfig({
  server: {
    port: 5173,
    open: true,
    proxy: {
      '/API': {
        target: 'http://127.0.0.1:5002',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/API/, ''),
      },
      // Forward DataStorage requests to the backend so we get actual JSON, not Vite's index.html fallback
      '/DataStorage': {
        target: 'http://127.0.0.1:5002',
        changeOrigin: true,
      },
      // Forward the Wijmo statically requested license to the backend
      '/References/wijmo/licence.js': {
        target: 'http://127.0.0.1:5002',
        changeOrigin: true,
      }
    },
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
});
