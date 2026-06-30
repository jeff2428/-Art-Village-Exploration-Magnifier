import { defineConfig } from 'vitest/config'

const projectRoot = decodeURIComponent(new URL('.', import.meta.url).pathname)
  .replace(/^\/([A-Za-z]:\/)/, '$1')

export default defineConfig({
  root: projectRoot,
  test: {
    environment: 'jsdom',
    include: ['src/**/*.test.{ts,tsx}'],
  },
})
