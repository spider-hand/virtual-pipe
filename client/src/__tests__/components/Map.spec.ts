import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'

import Map from '@/components/Map.vue'

const { fitBounds } = vi.hoisted(() => ({ fitBounds: vi.fn<() => void>() }))

vi.mock('maplibre-gl', () => ({
  Map: class {
    fitBounds = fitBounds
    remove = vi.fn<() => void>()
  },
  setWorkerUrl: vi.fn<() => void>(),
}))

describe('Map', () => {
  afterEach(() => {
    vi.useRealTimers()
    vi.unstubAllGlobals()
  })

  it('should fit the map to the district selected from search', async () => {
    vi.useFakeTimers()
    const bounds = [139.5, 35.4, 139.7, 35.5]
    const fetch = vi
      .fn<typeof globalThis.fetch>()
      .mockResolvedValue(Response.json([{ code: '14104', label: '神奈川県 横浜市 中区', bounds }]))
    vi.stubGlobal('fetch', fetch)

    const wrapper = mount(Map)
    const input = wrapper.get('input')

    await input.trigger('focus')
    await input.setValue('横浜市')
    await vi.advanceTimersByTimeAsync(200)
    await flushPromises()
    await wrapper.get('[role="option"]').trigger('click')

    expect(fitBounds).toHaveBeenCalledExactlyOnceWith(bounds, { padding: 48 })
    expect(fetch).toHaveBeenCalledTimes(1)

    wrapper.unmount()
  })
})
