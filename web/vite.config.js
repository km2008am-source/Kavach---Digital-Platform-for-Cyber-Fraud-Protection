import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Dev only: send API, static and health calls to the FastAPI app so the browser sees one origin.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8000',
      '/static': 'http://localhost:8000',
      '/health': 'http://localhost:8000',
    },
  },
  test: { environment: 'node', include: ['src/**/*.test.js'] },
})
