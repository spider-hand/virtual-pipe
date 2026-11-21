import { flushPromises } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { VueQueryPlugin } from '@tanstack/vue-query'
import { createApp, effectScope } from 'vue'

import { usePipeSetsQuery } from '@/composables/usePipeSetsQuery'
import { createQueryClient } from '@/queryClient'

const id = '7fc19571-3276-49e3-9ef0-4ccb7cd1d599'
const selection = {
  name: 'Demo mains',
  districtId: '01404',
  attributeSetId: '4984ce93-5b72-473c-ae9e-950b46d4f9c8',
}

describe('usePipeSetsQuery', () => {
  const onSucceeded = vi.fn<(id: string) => void>()
  let scope: ReturnType<typeof effectScope>
  let fetch: ReturnType<typeof vi.fn<typeof globalThis.fetch>>
  let query: ReturnType<typeof usePipeSetsQuery>

  beforeEach(() => {
    vi.useFakeTimers()
    onSucceeded.mockClear()
    fetch = vi
      .fn<typeof globalThis.fetch>()
      .mockResolvedValueOnce(Response.json({ id }, { status: 202 }))
    vi.stubGlobal('fetch', fetch)
    scope = effectScope()
    const app = createApp({}).use(VueQueryPlugin, { queryClient: createQueryClient() })
    query = app.runWithContext(() => scope.run(() => usePipeSetsQuery({ onSucceeded }))!)
  })

  afterEach(() => {
    scope.stop()
    vi.useRealTimers()
    vi.unstubAllGlobals()
  })

  it('should submit once and check every ten seconds without overlapping requests', async () => {
    let finishPoll!: (response: Response) => void
    fetch
      .mockImplementationOnce(
        () =>
          new Promise((resolve) => {
            finishPoll = resolve
          }),
      )
      .mockResolvedValueOnce(Response.json({ id, status: 'succeeded' }))

    const submitting = query.createPipeSet(selection)
    expect(query.isPipeSetBusy.value).toBe(true)
    await query.createPipeSet(selection)
    await submitting
    await query.createPipeSet(selection)

    await vi.advanceTimersByTimeAsync(9_999)
    expect(fetch).toHaveBeenCalledTimes(1)
    await vi.advanceTimersByTimeAsync(1)
    expect(fetch).toHaveBeenLastCalledWith(
      `/api/pipesets/${id}/`,
      expect.objectContaining({ method: 'GET', cache: 'no-store' }),
    )
    await vi.advanceTimersByTimeAsync(20_000)
    expect(fetch).toHaveBeenCalledTimes(2)

    finishPoll(Response.json({ id, status: 'pending' }))
    await flushPromises()
    await vi.advanceTimersByTimeAsync(10_000)
    expect(onSucceeded).toHaveBeenCalledExactlyOnceWith(id)
    expect(query.isPipeSetBusy.value).toBe(false)
    await vi.advanceTimersByTimeAsync(20_000)
    expect(fetch).toHaveBeenCalledTimes(3)
  })

  it('should continue checking the same job after a temporary error', async () => {
    fetch
      .mockResolvedValueOnce(new Response(null, { status: 503 }))
      .mockResolvedValueOnce(Response.json({ id, status: 'pending' }))
    await query.createPipeSet(selection)

    await vi.advanceTimersByTimeAsync(10_000)
    expect(query.pipeSetStatus.value).toBe('statusUnavailable')
    expect(query.isPipeSetBusy.value).toBe(true)
    await vi.advanceTimersByTimeAsync(10_000)
    expect(query.pipeSetStatus.value).toBe('pending')
    expect(fetch).toHaveBeenCalledTimes(3)
    expect(fetch.mock.calls.slice(1).map(([url]) => url)).toEqual([
      `/api/pipesets/${id}/`,
      `/api/pipesets/${id}/`,
    ])
  })

  it.each([
    ['failed', () => Response.json({ id, status: 'failed' })],
    ['notFound', () => new Response(null, { status: 404 })],
  ])(
    'should stop checking without displaying pipes when the status is %s',
    async (status, response) => {
      fetch.mockResolvedValueOnce(response())
      await query.createPipeSet(selection)
      await vi.advanceTimersByTimeAsync(30_000)

      expect(query.pipeSetStatus.value).toBe(status)
      expect(query.isPipeSetBusy.value).toBe(false)
      expect(onSucceeded).not.toHaveBeenCalled()
      expect(fetch).toHaveBeenCalledTimes(2)
    },
  )

  it('should cancel the scheduled status check on unmount', async () => {
    await query.createPipeSet(selection)
    scope.stop()
    await vi.advanceTimersByTimeAsync(30_000)

    expect(fetch).toHaveBeenCalledOnce()
  })

  it('should abort an in-flight status check on unmount', async () => {
    let finishPoll!: (response: Response) => void
    fetch.mockImplementationOnce(
      () =>
        new Promise((resolve) => {
          finishPoll = resolve
        }),
    )
    await query.createPipeSet(selection)
    await vi.advanceTimersByTimeAsync(10_000)

    const [, options] = fetch.mock.calls[1]!
    scope.stop()
    expect(options?.signal?.aborted).toBe(true)
    finishPoll(Response.json({ id, status: 'succeeded' }))
    await flushPromises()
    expect(onSucceeded).not.toHaveBeenCalled()
  })
})
