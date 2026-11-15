import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'

import PipeSetGenerator from '@/components/PipeSetGenerator.vue'
import { createTestPlugins } from '@/__tests__/testSetup'

const set = {
  id: 'a4c52712-4dd2-4510-91d7-69786a55d114',
  name: 'Water mains',
  attributes: [
    { name: 'material', type: 'string', choices: ['PVC', '鋼'] },
    { name: 'pressure', type: 'decimal', min: '1.20', max: '2.00' },
    { name: 'pipe_id', type: 'id', id_format: 'sequential' },
  ],
}
const district = { code: '01404', label: '北海道 神恵内村', bounds: [140.3, 43.1, 140.5, 43.2] }

afterEach(() => {
  vi.useRealTimers()
  vi.unstubAllGlobals()
})

describe('PipeSetGenerator', () => {
  it('should render the default state', () => {
    const wrapper = mount(PipeSetGenerator, {
      global: { plugins: createTestPlugins() },
      props: { active: false },
    })

    expect(wrapper.get<HTMLInputElement>('input[value="district"]').element.checked).toBe(true)
    expect(wrapper.get('[role="combobox"]').attributes('placeholder')).toBe(
      'Prefecture, city, or ward',
    )
    expect(wrapper.find('input[placeholder="Prefecture name"]').exists()).toBe(false)
    expect(wrapper.get('input[required]').element.value).toBe('')
    expect(wrapper.find('[role="alert"]').exists()).toBe(false)
    expect(wrapper.get('select').element.value).toBe('')
    expect(wrapper.find('h2').exists()).toBe(false)
    expect(wrapper.get('button').element.disabled).toBe(true)

    wrapper.unmount()
  })

  it.each(['', '   '])(
    'should show a required error on leaving the name field with %j',
    async (value) => {
      const wrapper = mount(PipeSetGenerator, {
        global: { plugins: createTestPlugins() },
        props: { active: false },
      })
      const name = wrapper.get('input[required]')

      await name.setValue(value)
      expect(wrapper.find('[role="alert"]').exists()).toBe(false)
      await name.trigger('blur')

      const error = wrapper.get('[role="alert"]')
      expect(error.text()).toBe('Enter a pipe set name.')
      expect(name.attributes('aria-invalid')).toBe('true')
      expect(name.attributes('aria-describedby')).toBe(error.attributes('id'))

      await name.setValue('Demo mains')
      expect(wrapper.find('[role="alert"]').exists()).toBe(false)
      wrapper.unmount()
    },
  )

  it('should show an error and disable selection when the attribute sets fail to load', async () => {
    const fetch = vi
      .fn<typeof globalThis.fetch>()
      .mockResolvedValueOnce(new Response(null, { status: 503 }))
    vi.stubGlobal('fetch', fetch)
    const wrapper = mount(PipeSetGenerator, {
      global: { plugins: createTestPlugins() },
      props: { active: true },
    })

    expect(wrapper.get('[role="status"]').text()).toBe('Loading attribute sets…')
    await flushPromises()
    expect(wrapper.get('[role="alert"]').text()).toBe('Could not load attribute sets.')

    expect(wrapper.get('select').element.disabled).toBe(true)
    expect(wrapper.findAll('button').map((button) => button.text())).toEqual(['Save Pipe Set'])
    expect(wrapper.get('button.save').element.disabled).toBe(true)

    wrapper.unmount()
  })

  it('should guide users to create an attribute set when the list is empty', async () => {
    vi.stubGlobal('fetch', vi.fn<typeof fetch>().mockResolvedValue(Response.json([])))
    const wrapper = mount(PipeSetGenerator, {
      global: { plugins: createTestPlugins() },
      props: { active: true },
    })
    await flushPromises()

    expect(wrapper.get('[role="status"]').text()).toContain('Create an attribute set')
    expect(wrapper.get('select').element.disabled).toBe(true)
    expect(wrapper.get('button.save').element.disabled).toBe(true)

    wrapper.unmount()
  })

  it('should preview definitions in order and keep the selected set when the tab is revisited', async () => {
    const nextSet = { ...set, id: 'cd901b32-52c2-4f2d-a994-6ecd94a66530', name: 'New set' }
    const fetch = vi
      .fn<typeof globalThis.fetch>()
      .mockResolvedValueOnce(Response.json([set]))
      .mockResolvedValueOnce(Response.json([]))
      .mockResolvedValueOnce(Response.json([nextSet, set]))
    vi.stubGlobal('fetch', fetch)
    const wrapper = mount(PipeSetGenerator, {
      global: { plugins: createTestPlugins() },
      props: { active: true },
    })
    await flushPromises()

    const select = wrapper.get('select')
    await select.setValue(set.id)
    expect(wrapper.findAll('dt').map((term) => term.text())).toEqual([
      'material',
      'pressure',
      'pipe_id',
    ])
    expect(wrapper.findAll('dd').map((definition) => definition.text())).toEqual([
      'String',
      'PVC, 鋼',
      'Decimal',
      '1.20 to 2.00',
      'Generated ID',
      'Sequential',
    ])

    await wrapper.setProps({ active: false })
    await wrapper.setProps({ active: true })
    await flushPromises()

    expect(select.element.value).toBe(set.id)
    expect(select.findAll('option').map((option) => option.text())).toContain('New set')

    wrapper.unmount()
  })

  it('should validate untouched fields before requesting a save', async () => {
    const fetch = vi.fn<typeof globalThis.fetch>().mockResolvedValue(Response.json([set]))
    vi.stubGlobal('fetch', fetch)
    const wrapper = mount(PipeSetGenerator, {
      global: { plugins: createTestPlugins() },
      props: { active: true },
      attachTo: document.body,
    })
    await flushPromises()

    const save = wrapper.get('button.save')
    expect(save.element.disabled).toBe(false)
    expect(wrapper.find('[role="alert"]').exists()).toBe(false)

    await save.trigger('click')

    expect(wrapper.findAll('[role="alert"]').map((alert) => alert.text())).toEqual([
      'Enter a pipe set name.',
      'Select an attribute set.',
      'Select a district.',
    ])
    expect(fetch).toHaveBeenCalledTimes(2)

    const select = wrapper.get('select')
    await select.setValue(set.id)
    expect(select.attributes('aria-invalid')).toBeUndefined()

    wrapper.unmount()
  })

  it('should require a valid name and preserve the form if submission fails', async () => {
    vi.useFakeTimers()
    const fetch = vi
      .fn<typeof globalThis.fetch>()
      .mockResolvedValueOnce(Response.json([set]))
      .mockResolvedValueOnce(Response.json([]))
      .mockResolvedValueOnce(Response.json([district]))
      .mockResolvedValueOnce(new Response(null, { status: 503 }))
    vi.stubGlobal('fetch', fetch)
    const wrapper = mount(PipeSetGenerator, {
      global: { plugins: createTestPlugins() },
      props: { active: true },
    })
    await flushPromises()
    const select = wrapper.get('select')
    const name = wrapper.get('input[required]')
    const search = wrapper.get('input[role="combobox"]')
    const save = wrapper.get('button.save')

    await select.setValue(set.id)
    expect(save.element.disabled).toBe(false)
    await search.trigger('focus')
    await search.setValue('神恵内村')
    await vi.advanceTimersByTimeAsync(200)
    await wrapper.get('[role="option"]').trigger('click')
    expect(save.element.disabled).toBe(false)
    await wrapper.get('form').trigger('submit')
    expect(wrapper.get('[role="alert"]').text()).toBe('Enter a pipe set name.')
    expect(fetch).toHaveBeenCalledTimes(3)

    await name.setValue('管'.repeat(256))
    expect(wrapper.get('[role="alert"]').text()).toBe('Use 255 characters or fewer.')
    await wrapper.get('form').trigger('submit')
    expect(fetch).toHaveBeenCalledTimes(3)

    await name.setValue('  Demo mains  ')
    expect(save.element.disabled).toBe(false)

    await wrapper.get('form').trigger('submit')
    await flushPromises()
    expect(fetch).toHaveBeenLastCalledWith(
      '/api/pipesets/',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({
          name: 'Demo mains',
          district_id: district.code,
          attribute_set_id: set.id,
        }),
      }),
    )
    expect(wrapper.get('[role="status"]').text()).toBe('Could not submit the pipe set. Try again.')
    expect(select.element.value).toBe(set.id)
    expect(search.element.value).toBe(district.label)
    expect(name.element.value).toBe('  Demo mains  ')
    expect(save.element.disabled).toBe(false)

    await search.setValue('北海道')
    expect(save.element.disabled).toBe(false)
    await wrapper.get('form').trigger('submit')
    expect(wrapper.get('[role="alert"]').text()).toBe('Select a district.')
    expect(fetch).toHaveBeenCalledTimes(4)

    wrapper.unmount()
  })

  it('should preload prefectures, filter locally, and submit only an explicitly chosen prefecture', async () => {
    const prefecture = { code: '01', label: '北海道', bounds: [139, 41, 146, 46] }
    const other = { code: '02', label: 'テスト県', bounds: [140, 40, 142, 42] }
    const fetch = vi
      .fn<typeof globalThis.fetch>()
      .mockResolvedValueOnce(Response.json([set]))
      .mockResolvedValueOnce(Response.json([prefecture, other]))
      .mockResolvedValueOnce(Response.json({ id: set.id }, { status: 202 }))
    vi.stubGlobal('fetch', fetch)
    const wrapper = mount(PipeSetGenerator, {
      global: { plugins: createTestPlugins() },
      props: { active: false },
    })

    expect(fetch).not.toHaveBeenCalled()
    await wrapper.setProps({ active: true })
    await flushPromises()
    expect(fetch).toHaveBeenCalledWith(
      '/api/prefectures/',
      expect.objectContaining({ method: 'GET' }),
    )
    expect(wrapper.find('input[placeholder="Prefecture name"]').exists()).toBe(false)

    await wrapper.get('input[value="prefecture"]').setValue()
    const search = wrapper.get('input[role="combobox"]')
    await search.trigger('focus')
    expect(wrapper.findAll('[role="option"]').map((option) => option.text())).toEqual([
      prefecture.label,
      other.label,
    ])
    await search.setValue('該当なし')
    expect(wrapper.get('[role="status"]').text()).toBe('No matching prefectures')
    await search.setValue('　ﾃ ｽ ﾄ　')
    expect(wrapper.get('[role="option"]').text()).toBe(other.label)
    await search.setValue('北 海')
    expect(wrapper.get('[role="option"]').text()).toBe(prefecture.label)

    await wrapper.get('input[required]').setValue('Wide area')
    await wrapper.get('select').setValue(set.id)
    await search.trigger('keydown', { key: 'Enter' })
    await wrapper.get('form').trigger('submit')
    expect(wrapper.get('[role="alert"]').text()).toBe('Select a prefecture.')
    expect(fetch).toHaveBeenCalledTimes(2)
    expect(wrapper.emitted('areaChange')).toBeUndefined()

    await search.trigger('keydown', { key: 'ArrowDown' })
    await search.trigger('keydown', { key: 'Enter' })
    expect(wrapper.emitted('areaChange')).toEqual([[prefecture]])

    await wrapper.get('input[value="district"]').setValue()
    expect(wrapper.emitted('areaChange')).toEqual([[prefecture], [null]])
    await wrapper.get('input[value="prefecture"]').setValue()
    const newSearch = wrapper.get('input[role="combobox"]')
    expect(newSearch.element.value).toBe('')
    await newSearch.trigger('focus')
    await wrapper.get('[role="option"]:first-child').trigger('click')

    await wrapper.get('form').trigger('submit')
    await flushPromises()
    expect(fetch).toHaveBeenCalledTimes(3)
    expect(fetch).toHaveBeenLastCalledWith(
      '/api/pipesets/',
      expect.objectContaining({
        body: JSON.stringify({
          name: 'Wide area',
          prefecture_id: '01',
          attribute_set_id: set.id,
        }),
      }),
    )
    expect(wrapper.get('fieldset').element.disabled).toBe(true)
    expect(newSearch.element.disabled).toBe(true)
    wrapper.unmount()
  })
})
