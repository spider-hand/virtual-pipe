import { enableAutoUnmount, flushPromises, mount, RouterLinkStub } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'

import RoadDataSetupPage from '@/pages/RoadDataSetupPage.vue'
import { createTestPlugins } from '@/__tests__/testSetup'

const coverage = {
  regions: ['kanto', 'shikoku', 'tohoku'],
  cached_regions: ['kanto', 'shikoku'],
  has_roads: true,
  active_region: 'kanto',
}

const job = { id: 1, region: 'shikoku', failure: null }

const mountPage = () =>
  mount(RoadDataSetupPage, {
    global: { plugins: createTestPlugins(), stubs: { RouterLink: RouterLinkStub } },
  })

enableAutoUnmount(afterEach)

describe('RoadDataSetupPage', () => {
  afterEach(() => {
    vi.useRealTimers()
    vi.unstubAllGlobals()
  })

  it('should render the default state', async () => {
    vi.stubGlobal(
      'fetch',
      vi
        .fn<typeof globalThis.fetch>()
        .mockResolvedValue(
          Response.json({ ...coverage, has_roads: false, active_region: null, setup: null }),
        ),
    )

    const wrapper = mountPage()
    await flushPromises()

    expect(wrapper.text()).toContain('No road data is active.')
    expect(wrapper.get('select').element.value).toBe('')
    expect(wrapper.get('button[type="submit"]').element).toHaveProperty('disabled', true)
  })

  it.each([
    { region: 'kanto', label: 'Already active', disabled: true },
    { region: 'shikoku', label: 'Activate', disabled: false },
    { region: 'tohoku', label: 'Download and activate', disabled: false },
  ])('should show $label when selecting $region', async ({ region, label, disabled }) => {
    vi.stubGlobal(
      'fetch',
      vi
        .fn<typeof globalThis.fetch>()
        .mockResolvedValue(Response.json({ ...coverage, setup: null })),
    )

    const wrapper = mountPage()
    await flushPromises()
    await wrapper.get('select').setValue(region)

    const button = wrapper.get('button[type="submit"]')
    expect(button.text()).toBe(label)
    expect(button.element).toHaveProperty('disabled', disabled)
  })

  it('should refresh the active region after a setup conflict', async () => {
    vi.stubGlobal(
      'fetch',
      vi
        .fn<typeof globalThis.fetch>()
        .mockResolvedValueOnce(Response.json({ ...coverage, setup: null }))
        .mockResolvedValueOnce(new Response(null, { status: 409 }))
        .mockResolvedValueOnce(
          Response.json({ ...coverage, active_region: 'shikoku', setup: null }),
        ),
    )

    const wrapper = mountPage()
    await flushPromises()
    await wrapper.get('select').setValue('shikoku')
    await wrapper.get('form').trigger('submit')
    await flushPromises()

    expect(wrapper.text()).toContain('Active region: Shikoku')
    expect(wrapper.get('button[type="submit"]').text()).toBe('Already active')
    expect(wrapper.text()).not.toContain('already in progress')
  })

  it('should start setup for the selected region and prevent another submission', async () => {
    const fetch = vi
      .fn<typeof globalThis.fetch>()
      .mockResolvedValueOnce(Response.json({ ...coverage, setup: null }))
      .mockResolvedValueOnce(Response.json({ ...job, status: 'queued' }, { status: 202 }))
    vi.stubGlobal('fetch', fetch)

    const wrapper = mountPage()
    await flushPromises()
    await wrapper.get('select').setValue('shikoku')
    await wrapper.get('form').trigger('submit')
    await flushPromises()

    expect(fetch).toHaveBeenLastCalledWith(
      '/api/road-data/setups/',
      expect.objectContaining({ method: 'POST', body: '{"region":"shikoku"}' }),
    )
    expect(wrapper.text()).toContain('Waiting to prepare roads for Shikoku')
    expect(wrapper.get('button[type="submit"]').element).toHaveProperty('disabled', true)
  })

  it('should resume progress on entry and update coverage when import finishes', async () => {
    vi.useFakeTimers()
    vi.stubGlobal(
      'fetch',
      vi
        .fn<typeof globalThis.fetch>()
        .mockResolvedValueOnce(
          Response.json({ ...coverage, setup: { ...job, status: 'importing' } }),
        )
        .mockResolvedValueOnce(
          Response.json({
            ...coverage,
            active_region: 'shikoku',
            setup: { ...job, status: 'succeeded' },
          }),
        ),
    )

    const wrapper = mountPage()
    await vi.advanceTimersByTimeAsync(0)

    expect(wrapper.text()).toContain('Active region: Kanto')
    expect(wrapper.text()).toContain('Importing roads for Shikoku')

    await vi.advanceTimersByTimeAsync(2_001)

    expect(wrapper.text()).toContain('Active region: Shikoku')
    expect(wrapper.text()).not.toContain('Importing roads for Shikoku')
  })

  it('should show the failed region and allow a retry', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn<typeof globalThis.fetch>().mockResolvedValue(
        Response.json({
          ...coverage,
          setup: { ...job, status: 'failed', failure: 'import' },
        }),
      ),
    )

    const wrapper = mountPage()
    await flushPromises()

    expect(wrapper.text()).toContain('Active region: Kanto')
    expect(wrapper.text()).toContain('Could not import roads for Shikoku. Try again.')
    expect(wrapper.get('select').element.value).toBe('shikoku')
    expect(wrapper.get('button[type="submit"]').element).toHaveProperty('disabled', false)
  })
})
