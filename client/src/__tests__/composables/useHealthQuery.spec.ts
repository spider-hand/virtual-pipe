import { afterEach, describe, expect, it, vi } from 'vitest'

import { useHealthQuery } from '@/composables/useHealthQuery'

afterEach(() => vi.unstubAllGlobals())

describe('useHealthQuery', () => {
  it('should expose the health response', async () => {
    const fetch = vi
      .fn<typeof globalThis.fetch>()
      .mockResolvedValue(Response.json({ status: 'ok' }))
    vi.stubGlobal('fetch', fetch)
    const { data, error, checkHealth } = useHealthQuery()

    await checkHealth()

    expect(fetch).toHaveBeenCalledExactlyOnceWith(
      '/api/health/',
      expect.objectContaining({ method: 'GET' }),
    )
    expect(data.value).toEqual({ status: 'ok' })
    expect(error.value).toBeUndefined()
  })

  it('should expose a failed health request', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn<typeof fetch>().mockRejectedValue(new Error('Connection unavailable')),
    )
    const { data, error, checkHealth } = useHealthQuery()

    await checkHealth()

    expect(data.value).toBeUndefined()
    expect(error.value).toBeInstanceOf(Error)
  })
})
