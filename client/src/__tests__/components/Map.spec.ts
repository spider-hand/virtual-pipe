import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'

import Map from '@/components/Map.vue'

const { fitBounds, setData } = vi.hoisted(() => ({
  fitBounds: vi.fn<() => void>(),
  setData: vi.fn<() => void>(),
}))

vi.mock('maplibre-gl', () => ({
  Map: class {
    fitBounds = fitBounds
    getSource = () => ({ setData })
    once = vi.fn<() => void>()
    remove = vi.fn<() => void>()
  },
  setWorkerUrl: vi.fn<() => void>(),
}))

describe('Map', () => {
  afterEach(() => {
    vi.useRealTimers()
    vi.unstubAllGlobals()
  })

  it('should fit and highlight the chosen district until the search text is edited', async () => {
    vi.useFakeTimers()
    const bounds = [139.5, 35.4, 139.7, 35.5]
    const fetch = vi
      .fn<typeof globalThis.fetch>()
      .mockResolvedValueOnce(Response.json([]))
      .mockResolvedValueOnce(
        Response.json([{ code: '14104', label: '神奈川県 横浜市 中区', bounds }]),
      )
    vi.stubGlobal('fetch', fetch)

    const wrapper = mount(Map)
    const panel = wrapper.get('[role="tabpanel"]:has([role="combobox"])')
    expect(panel.isVisible()).toBe(false)
    await wrapper.get('[role="tab"][aria-controls$="-generate"]').trigger('click')
    const input = wrapper.get('input[role="combobox"]')

    await input.trigger('focus')
    await input.setValue('横浜市')
    await vi.advanceTimersByTimeAsync(200)
    await flushPromises()
    await wrapper.get('[role="option"]').trigger('click')

    expect(fitBounds).toHaveBeenCalledExactlyOnceWith(bounds, { padding: 48 })
    expect(setData).toHaveBeenLastCalledWith({
      type: 'Polygon',
      coordinates: [
        [
          [139.5, 35.4],
          [139.7, 35.4],
          [139.7, 35.5],
          [139.5, 35.5],
          [139.5, 35.4],
        ],
      ],
    })

    await input.setValue('横浜')
    expect(setData).toHaveBeenLastCalledWith({ type: 'FeatureCollection', features: [] })

    wrapper.unmount()
  })
})
