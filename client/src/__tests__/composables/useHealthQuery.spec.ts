import { VueQueryPlugin } from '@tanstack/vue-query'
import { createApp, effectScope } from 'vue'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { useHealthQuery } from '@/composables/useHealthQuery'

import { createQueryClient } from '@/queryClient'

describe('useHealthQuery', () => {
  let scope: ReturnType<typeof effectScope>
  let query: ReturnType<typeof useHealthQuery>

  beforeEach(() => {
    scope = effectScope()
    const app = createApp({}).use(VueQueryPlugin, { queryClient: createQueryClient() })
    query = app.runWithContext(() => scope.run(useHealthQuery)!)
  })

  afterEach(() => {
    scope.stop()
    vi.unstubAllGlobals()
  })

  it('should expose the health response', async () => {
    const fetch = vi
      .fn<typeof globalThis.fetch>()
      .mockResolvedValue(Response.json({ status: 'ok' }))
    vi.stubGlobal('fetch', fetch)
    const { data, error, checkHealth } = query

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
    const { data, error, checkHealth } = query

    await checkHealth()

    expect(data.value).toBeUndefined()
    expect(error.value).toBeInstanceOf(Error)
  })
})
