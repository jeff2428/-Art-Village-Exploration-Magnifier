import { describe, expect, it } from 'vitest'
import serviceWorkerSource from '../../public/sw.js?raw'

describe('service worker navigation policy', () => {
  it('fetches navigations from the network before using the cached app shell', () => {
    expect(serviceWorkerSource).toContain("event.request.mode === 'navigate'")
    expect(serviceWorkerSource.indexOf('fetch(event.request)')).toBeLessThan(
      serviceWorkerSource.indexOf("caches.match('/index.html')"),
    )
  })
})
