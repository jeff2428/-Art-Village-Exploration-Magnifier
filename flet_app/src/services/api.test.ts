import { describe, expect, it } from 'vitest'
import { API_URL } from './api'

describe('API_URL', () => {
  it('falls back to the production Worker when no build-time URL is configured', () => {
    expect(API_URL).toBe('https://art-village-magnifier.jeff2428.workers.dev')
  })
})
