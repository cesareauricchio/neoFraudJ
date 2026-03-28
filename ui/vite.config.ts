import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,   // Required for Docker — binds to 0.0.0.0
    port: 5173,
  },
})
