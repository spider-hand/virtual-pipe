import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'

import DistrictSearch from '@/components/DistrictSearch.vue'
import { createTestPlugins } from '@/__tests__/testSetup'

const district = {
  code: '14104',
  label: '神奈川県 横浜市 中区',
  labelEn: 'Kanagawa Yokohamashi, Nakaku',
  bounds: [139.5, 35.4, 139.7, 35.5],
}

const districtResponse = {
  code: district.code,
  label: district.label,
  label_en: district.labelEn,
  bounds: district.bounds,
}

afterEach(() => {
  vi.useRealTimers()
  vi.unstubAllGlobals()
})

describe('DistrictSearch', () => {
  it('should render the default state', () => {
    const wrapper = mount(DistrictSearch, { global: { plugins: createTestPlugins() } })

    expect(wrapper.get('[role="combobox"]').attributes('aria-expanded')).toBe('false')
    expect(wrapper.find('[role="option"]').exists()).toBe(false)

    wrapper.unmount()
  })

  it.each(['keyboard', 'pointer'])(
    'should select a district by %s after IME input',
    async (method) => {
      vi.useFakeTimers()
      const fetch = vi
        .fn<typeof globalThis.fetch>()
        .mockResolvedValue(Response.json([districtResponse]))
      vi.stubGlobal('fetch', fetch)
      const wrapper = mount(DistrictSearch, { global: { plugins: createTestPlugins() } })
      const input = wrapper.get('input')

      await input.trigger('focus')
      await input.trigger('compositionstart')
      await input.setValue('横浜市')
      await vi.advanceTimersByTimeAsync(200)
      expect(fetch).not.toHaveBeenCalled()

      await input.trigger('compositionend')
      await vi.advanceTimersByTimeAsync(200)
      await flushPromises()
      expect(wrapper.get('[role="option"]').text()).toBe(district.label)

      if (method === 'keyboard') {
        await input.trigger('keydown', { key: 'ArrowDown' })
        await input.trigger('keydown', { key: 'Enter' })
      } else {
        await wrapper.get('[role="option"]').trigger('click')
      }

      expect(wrapper.emitted('select')).toEqual([[district]])
      expect(input.element.value).toBe(district.label)
      expect(input.attributes('aria-expanded')).toBe('false')

      wrapper.unmount()
    },
  )

  it('should keep the latest suggestions when an earlier search finishes last', async () => {
    vi.useFakeTimers()
    let completeFirstRequest!: (response: Response) => void
    const firstRequest = new Promise<Response>((resolve) => {
      completeFirstRequest = resolve
    })
    const latestDistrict = {
      code: '13206',
      label: '東京都 府中市',
      label_en: 'Tokyo Fuchushi',
      bounds: [139.42, 35.64, 139.53, 35.7],
    }
    const fetch = vi
      .fn<typeof globalThis.fetch>()
      .mockReturnValueOnce(firstRequest)
      .mockResolvedValueOnce(Response.json([latestDistrict]))
    vi.stubGlobal('fetch', fetch)
    const wrapper = mount(DistrictSearch, { global: { plugins: createTestPlugins() } })
    const input = wrapper.get('input')

    await input.trigger('focus')
    await input.setValue('横浜')
    await vi.advanceTimersByTimeAsync(200)
    await input.setValue('府中市')
    await vi.advanceTimersByTimeAsync(200)

    expect(wrapper.get('[role="option"]').text()).toBe(latestDistrict.label)

    completeFirstRequest(Response.json([districtResponse]))
    await flushPromises()

    expect(wrapper.findAll('[role="option"]').map((option) => option.text())).toEqual([
      latestDistrict.label,
    ])

    wrapper.unmount()
  })
})
