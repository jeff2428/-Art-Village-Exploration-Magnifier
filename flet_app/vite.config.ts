import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const projectRoot = decodeURIComponent(new URL('.', import.meta.url).pathname)
  .replace(/^\/([A-Za-z]:\/)/, '$1')

// https://vitejs.dev/config/
export default defineConfig({
  root: projectRoot,
  plugins: [react()],
  build: {
    outDir: 'build/web',
    emptyOutDir: true,
  },
})
