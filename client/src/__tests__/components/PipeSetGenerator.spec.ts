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

    wrapper.unmount()
  })

  it('should preview definitions in order and keep the selected set when the tab is revisited', async () => {
    const nextSet = { ...set, id: 'cd901b32-52c2-4f2d-a994-6ecd94a66530', name: 'New set' }
    const fetch = vi
      .fn<typeof globalThis.fetch>()
      .mockResolvedValueOnce(Response.json([set]))
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

  it('should require a valid name and preserve the form if submission fails', async () => {
    vi.useFakeTimers()
    const fetch = vi
      .fn<typeof globalThis.fetch>()
      .mockResolvedValueOnce(Response.json([set]))
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
    expect(save.element.disabled).toBe(true)
    await search.trigger('focus')
    await search.setValue('神恵内村')
    await vi.advanceTimersByTimeAsync(200)
    await wrapper.get('[role="option"]').trigger('click')
    expect(save.element.disabled).toBe(false)
    await wrapper.get('form').trigger('submit')
    expect(wrapper.get('[role="alert"]').text()).toBe('Enter a pipe set name.')
    expect(fetch).toHaveBeenCalledTimes(2)

    await name.setValue('管'.repeat(256))
    expect(wrapper.get('[role="alert"]').text()).toBe('Use 255 characters or fewer.')
    await wrapper.get('form').trigger('submit')
    expect(fetch).toHaveBeenCalledTimes(2)

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
    expect(save.element.disabled).toBe(true)

    wrapper.unmount()
  })
})
