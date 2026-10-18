import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/farmers': 'http://localhost:8000',
      '/schedule': 'http://localhost:8000',
      '/turn': 'http://localhost:8000',
      '/logs': 'http://localhost:8000',
      '/stats': 'http://localhost:8000',
      '/reset': 'http://localhost:8000'
    }
  }
});
