import { flushPromises, mount } from '@vue/test-utils'
import type { MapOptions } from 'maplibre-gl'
import { afterEach, describe, expect, it, vi } from 'vitest'

import Map from '@/components/Map.vue'
import PipeSidebar from '@/components/PipeSidebar.vue'
import { createAppI18n } from '@/i18n'

const global = { plugins: [createAppI18n('en')] }

const { fitBounds, setData, setTiles, createMap, onLoad, addSource, addLayer } = vi.hoisted(() => ({
  fitBounds: vi.fn<() => void>(),
  setData: vi.fn<() => void>(),
  setTiles: vi.fn<() => void>(),
  createMap: vi.fn<(options: MapOptions) => void>(),
  onLoad: vi.fn<(event: string, callback: () => void) => void>(),
  addSource: vi.fn<() => void>(),
  addLayer: vi.fn<() => void>(),
}))

vi.mock('maplibre-gl', () => ({
  Map: class {
    constructor(options: MapOptions) {
      createMap(options)
    }

    fitBounds = fitBounds
    getSource = (id: string) => {
      if (id === 'district-bounds') return { setData }
      if (id === 'pipes' && addSource.mock.calls.length) return { setTiles }
    }
    addSource = addSource
    addLayer = addLayer
    once = onLoad
    remove = vi.fn<() => void>()
  },
  setWorkerUrl: vi.fn<() => void>(),
}))

describe('Map', () => {
  afterEach(() => {
    vi.useRealTimers()
    vi.unstubAllGlobals()
    vi.clearAllMocks()
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

    const wrapper = mount(Map, { global })
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

  it('should load pipes only after generation succeeds, even with the sidebar closed', async () => {
    vi.useFakeTimers()
    const id = '7fc19571-3276-49e3-9ef0-4ccb7cd1d599'
    const attributeSetId = '4984ce93-5b72-473c-ae9e-950b46d4f9c8'
    const fetch = vi
      .fn<typeof globalThis.fetch>()
      .mockResolvedValueOnce(Response.json([{ id: attributeSetId, name: 'Mains', attributes: [] }]))
      .mockResolvedValueOnce(
        Response.json([{ code: '14104', label: '横浜市', bounds: [139.5, 35.4, 139.7, 35.5] }]),
      )
      .mockResolvedValueOnce(Response.json({ id }, { status: 202 }))
      .mockResolvedValueOnce(Response.json({ id, status: 'pending' }))
      .mockResolvedValueOnce(Response.json({ id, status: 'succeeded' }))
    vi.stubGlobal('fetch', fetch)

    const wrapper = mount(Map, { global })
    const style = createMap.mock.calls[0]![0].style
    expect(style).toMatchObject({ sources: { basemap: { type: 'raster' } } })
    expect(style && typeof style === 'object' && style.sources).not.toHaveProperty('pipes')
    onLoad.mock.calls[0]![1]()

    await wrapper.get('[role="tab"][aria-controls$="-generate"]').trigger('click')
    await flushPromises()
    const select = wrapper.get('.generator select')
    const search = wrapper.get('input[role="combobox"]')
    await select.setValue(attributeSetId)
    await search.trigger('focus')
    await search.setValue('横浜')
    await vi.advanceTimersByTimeAsync(200)
    await wrapper.get('[role="option"]').trigger('click')
    const save = wrapper.get('.generator button')
    await save.trigger('click')
    await flushPromises()
    expect(save.element.disabled).toBe(true)
    expect(select.element.disabled).toBe(true)
    expect(search.element.disabled).toBe(true)

    await wrapper.get('button[aria-label="Close pipe tools"]').trigger('click')
    await vi.advanceTimersByTimeAsync(10_000)
    expect(addSource).not.toHaveBeenCalled()
    await vi.advanceTimersByTimeAsync(10_000)
    expect(addSource).toHaveBeenCalledExactlyOnceWith(
      'pipes',
      expect.objectContaining({
        type: 'vector',
        tiles: [`${window.location.origin}/tiles/pipes/{z}/{x}/{y}?pipeset_id=${id}`],
      }),
    )
    expect(addLayer).toHaveBeenCalledExactlyOnceWith(
      expect.objectContaining({
        id: 'pipes',
        type: 'line',
        'source-layer': 'pipes',
      }),
    )

    const nextId = 'b7d35ae3-990c-45ad-9381-8de934f38f38'
    wrapper.getComponent(PipeSidebar).vm.$emit('pipesetReady', nextId)
    expect(setTiles).toHaveBeenCalledExactlyOnceWith([
      `${window.location.origin}/tiles/pipes/{z}/{x}/{y}?pipeset_id=${nextId}`,
    ])
    expect(addSource).toHaveBeenCalledOnce()
    wrapper.unmount()
  })
})
