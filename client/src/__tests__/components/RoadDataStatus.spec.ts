import { flushPromises, mount, RouterLinkStub } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'

import RoadDataStatus from '@/components/RoadDataStatus.vue'
import { createTestPlugins } from '@/__tests__/testSetup'

describe('RoadDataStatus', () => {
  afterEach(() => vi.unstubAllGlobals())

  it.each([
    { active_region: 'shikoku', has_roads: true, label: 'Shikoku' },
    { active_region: null, has_roads: true, label: 'Unknown' },
    { active_region: null, has_roads: false, label: 'No road data' },
  ])('should show $label for the current coverage', async ({ label, ...coverage }) => {
    vi.stubGlobal(
      'fetch',
      vi
        .fn<typeof globalThis.fetch>()
        .mockResolvedValue(
          Response.json({ ...coverage, regions: ['shikoku'], cached_regions: [], setup: null }),
        ),
    )

    const wrapper = mount(RoadDataStatus, {
      global: { plugins: createTestPlugins(), stubs: { RouterLink: RouterLinkStub } },
    })
    await flushPromises()

    expect(wrapper.get('[role="status"]').text()).toBe(label)
    wrapper.unmount()
  })
})
