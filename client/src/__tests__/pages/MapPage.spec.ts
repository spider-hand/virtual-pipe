import { flushPromises, mount, RouterLinkStub } from '@vue/test-utils'
import type { MapOptions } from 'maplibre-gl'
import { afterEach, describe, expect, it, vi } from 'vitest'

import App from '@/App.vue'
import PipeSidebar from '@/components/PipeSidebar.vue'
import MapPage from '@/pages/MapPage.vue'
import { router } from '@/router'
import { createTestPlugins } from '@/__tests__/testSetup'

const newest = { id: 'newest', name: 'Newest', bounds: [139.5, 35.4, 139.7, 35.5] }
const oldest = { id: 'oldest', name: 'Oldest', bounds: [130.5, 34.4, 130.7, 34.5] }
const legacy = { id: 'legacy', name: 'Legacy', bounds: null }
const tileUrl = (id: string) => `${window.location.origin}/tiles/pipes/{z}/{x}/{y}?pipeset_id=${id}`

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

const mountMap = () =>
  mount(MapPage, {
    global: {
      plugins: createTestPlugins(),
      stubs: { RouterLink: RouterLinkStub, RoadDataStatus: true },
    },
  })

describe('MapPage', () => {
  afterEach(() => {
    vi.useRealTimers()
    vi.unstubAllGlobals()
    vi.clearAllMocks()
  })

  it.each(['district', 'prefecture'])(
    'should fit and highlight the chosen %s until the search text is edited',
    async (areaType) => {
      vi.useFakeTimers()
      const bounds = [139.5, 35.4, 139.7, 35.5]
      const result = {
        code: areaType === 'district' ? '14104' : '14',
        label: areaType === 'district' ? '神奈川県 横浜市 中区' : '神奈川県',
        bounds,
      }
      const fetch = vi
        .fn<typeof globalThis.fetch>()
        .mockResolvedValueOnce(Response.json([]))
        .mockResolvedValueOnce(Response.json([]))
        .mockResolvedValueOnce(Response.json(areaType === 'prefecture' ? [result] : []))
        .mockResolvedValueOnce(Response.json([result]))
      vi.stubGlobal('fetch', fetch)

      const wrapper = mountMap()
      const panel = wrapper.get('[role="tabpanel"]:has([role="combobox"])')
      expect(panel.isVisible()).toBe(false)
      await wrapper.get('[role="tab"][aria-controls$="-generate"]').trigger('click')
      if (areaType === 'prefecture') {
        await wrapper.get('input[value="prefecture"]').setValue()
      }
      const input = wrapper.get('input[role="combobox"]')

      await input.trigger('focus')
      if (areaType === 'district') {
        await input.setValue('横浜市')
        await vi.advanceTimersByTimeAsync(200)
      }
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
    },
  )

  it('should start with the newest pipeset and fit the map to another selected pipeset', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn<typeof fetch>().mockResolvedValue(Response.json([newest, oldest, legacy])),
    )
    const wrapper = mountMap()
    await flushPromises()
    const picker = wrapper.get('.selector select')

    expect(picker.element.value).toBe(newest.id)
    expect(addSource).not.toHaveBeenCalled()
    onLoad.mock.calls[0]![1]()
    expect(fitBounds).toHaveBeenLastCalledWith(newest.bounds, { padding: 48 })
    expect(addSource).toHaveBeenCalledWith(
      'pipes',
      expect.objectContaining({
        tiles: [tileUrl(newest.id)],
      }),
    )

    await picker.setValue(oldest.id)
    expect(fitBounds).toHaveBeenLastCalledWith(oldest.bounds, { padding: 48 })
    expect(setTiles).toHaveBeenLastCalledWith([tileUrl(oldest.id)])

    await picker.setValue(legacy.id)
    expect(fitBounds).toHaveBeenCalledTimes(2)
    expect(setTiles).toHaveBeenLastCalledWith([tileUrl(legacy.id)])
    wrapper.unmount()
  })

  it('should keep the selected pipe set and map when returning from road data setup', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn<typeof fetch>().mockImplementation(async (url) =>
        url === '/api/road-data/'
          ? Response.json({
              regions: ['shikoku'],
              has_roads: true,
              active_region: 'shikoku',
              cached_regions: ['shikoku'],
              setup: null,
            })
          : Response.json([newest, oldest]),
      ),
    )
    await router.push({ name: 'map' })
    const wrapper = mount(App, { global: { plugins: [...createTestPlugins(), router] } })
    await flushPromises()

    await wrapper.get('.selector select').setValue(oldest.id)
    await wrapper.get('a[href="/setup"]').trigger('click')
    await flushPromises()
    expect(wrapper.get('h1').text()).toBe('Road data')

    await wrapper.get('a[href="/"]').trigger('click')
    await flushPromises()
    expect(wrapper.get('.selector select').element.value).toBe(oldest.id)
    expect(createMap).toHaveBeenCalledTimes(1)

    wrapper.unmount()
  })

  it('should load pipes only after generation succeeds, even with the sidebar closed', async () => {
    vi.useFakeTimers()
    const id = '7fc19571-3276-49e3-9ef0-4ccb7cd1d599'
    const attributeSetId = '4984ce93-5b72-473c-ae9e-950b46d4f9c8'
    const fetch = vi
      .fn<typeof globalThis.fetch>()
      .mockResolvedValueOnce(Response.json([]))
      .mockResolvedValueOnce(Response.json([{ id: attributeSetId, name: 'Mains', attributes: [] }]))
      .mockResolvedValueOnce(Response.json([]))
      .mockResolvedValueOnce(
        Response.json([{ code: '14104', label: '横浜市', bounds: [139.5, 35.4, 139.7, 35.5] }]),
      )
      .mockResolvedValueOnce(Response.json({ id }, { status: 202 }))
      .mockResolvedValueOnce(Response.json({ id, status: 'pending' }))
      .mockResolvedValueOnce(Response.json({ id, status: 'succeeded' }))
      .mockResolvedValueOnce(Response.json([newest, { ...oldest, id }]))
    vi.stubGlobal('fetch', fetch)

    const wrapper = mountMap()
    const style = createMap.mock.calls[0]![0].style
    expect(style).toMatchObject({ sources: { basemap: { type: 'raster' } } })
    expect(style && typeof style === 'object' && style.sources).not.toHaveProperty('pipes')
    onLoad.mock.calls[0]![1]()

    await wrapper.get('[role="tab"][aria-controls$="-generate"]').trigger('click')
    await flushPromises()
    const picker = wrapper.get('.selector select')
    expect(picker.element.disabled).toBe(true)
    expect(picker.text()).toBe('No pipe sets yet')
    const select = wrapper.get('.generator select')
    const name = wrapper.get('.generator input[required]')
    const search = wrapper.get('input[role="combobox"]')
    await name.setValue('Demo mains')
    await select.setValue(attributeSetId)
    await search.trigger('focus')
    await search.setValue('横浜')
    await vi.advanceTimersByTimeAsync(200)
    await wrapper.get('[role="option"]').trigger('click')
    const save = wrapper.get('.generator button')
    await wrapper.get('form.generator').trigger('submit')
    await flushPromises()
    expect(save.element.disabled).toBe(true)
    expect(select.element.disabled).toBe(true)
    expect(name.element.disabled).toBe(true)
    expect(search.element.disabled).toBe(true)

    await wrapper.get('button[aria-label="Close pipe tools"]').trigger('click')
    await vi.advanceTimersByTimeAsync(10_000)
    expect(addSource).not.toHaveBeenCalled()
    await vi.advanceTimersByTimeAsync(10_000)
    expect(picker.element.value).toBe(id)
    expect(fetch).toHaveBeenLastCalledWith(
      '/api/pipesets/',
      expect.objectContaining({ method: 'GET', cache: 'no-store' }),
    )
    expect(fitBounds).toHaveBeenLastCalledWith(oldest.bounds, { padding: 48 })
    expect(addSource).toHaveBeenCalledExactlyOnceWith(
      'pipes',
      expect.objectContaining({
        type: 'vector',
        tiles: [tileUrl(id)],
      }),
    )
    expect(addLayer).toHaveBeenCalledExactlyOnceWith(
      expect.objectContaining({
        id: 'pipes',
        type: 'line',
        'source-layer': 'pipes',
      }),
    )

    wrapper.unmount()
  })

  it('should show a load error and keep the current pipes visible when refreshing fails', async () => {
    const fetch = vi
      .fn<typeof globalThis.fetch>()
      .mockResolvedValueOnce(Response.json([oldest]))
      .mockResolvedValueOnce(new Response(null, { status: 503 }))
    vi.stubGlobal('fetch', fetch)

    const wrapper = mountMap()
    await flushPromises()
    onLoad.mock.calls[0]![1]()
    const picker = wrapper.get('.selector select')

    wrapper.getComponent(PipeSidebar).vm.$emit('pipesetReady', newest.id)
    await flushPromises()
    expect(picker.element.value).toBe(oldest.id)
    expect(setTiles).not.toHaveBeenCalled()

    expect(wrapper.get('.selector [role="alert"]').text()).toBe('Could not load pipe sets.')
    expect(wrapper.find('.selector button').exists()).toBe(false)
    wrapper.unmount()
  })
})
