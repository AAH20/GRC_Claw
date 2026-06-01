import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  base: process.env.GRC_CLAW_CONSOLE_BASE ?? '/',
  server: {
    port: Number(process.env.GRC_CLAW_CONSOLE_PORT ?? 5174),
    proxy: {
      '/health': { target: 'http://127.0.0.1:18791', changeOrigin: true },
      '/api': { target: 'http://127.0.0.1:18791', changeOrigin: true },
    },
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
});
