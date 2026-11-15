import { mount } from '@vue/test-utils'
import { expect, it } from 'vitest'

import { createTestPlugins } from '@/__tests__/testSetup'
import PipeSetExport from '@/components/PipeSetExport.vue'
import type { PipeSetSummary } from '@/services'

const selectedSet: PipeSetSummary = {
  id: 'mains',
  name: 'Demo mains',
  bounds: null,
  attributeDefinitions: [{ name: 'material', type: 'string', choices: ['Steel', 'PVC'] }],
}
const legacySet: PipeSetSummary = {
  id: 'legacy',
  name: 'Legacy mains',
  bounds: null,
  attributeDefinitions: null,
}

it('should render the default state', () => {
  const wrapper = mount(PipeSetExport, { global: { plugins: createTestPlugins() } })

  expect(wrapper.text()).toContain('Select a pipe set to preview its attributes.')
  expect(wrapper.get('select').element.disabled).toBe(true)
  wrapper.unmount()
})

it('should preview the attribute definitions of the selected pipe set', () => {
  const wrapper = mount(PipeSetExport, {
    props: { selectedSet },
    global: { plugins: createTestPlugins() },
  })

  expect(wrapper.text()).toContain('Demo mains')
  expect(wrapper.text()).toContain('material')
  expect(wrapper.text()).toContain('Steel, PVC')
  wrapper.unmount()
})

it('should replace the preview with a message when the selected set has no definitions', async () => {
  const wrapper = mount(PipeSetExport, {
    props: { selectedSet },
    global: { plugins: createTestPlugins() },
  })

  await wrapper.setProps({ selectedSet: legacySet })

  expect(wrapper.text()).toContain('Legacy mains')
  expect(wrapper.text()).toContain('This pipe set has no attribute definitions.')
  expect(wrapper.text()).not.toContain('material')
  wrapper.unmount()
})

it('should offer CSV and Parquet and keep the chosen format when the pipe set changes', async () => {
  const wrapper = mount(PipeSetExport, {
    props: { selectedSet },
    global: { plugins: createTestPlugins() },
  })
  const format = wrapper.get('select')

  expect(format.element.disabled).toBe(false)
  expect(format.findAll('option').map((option) => option.text())).toEqual(['CSV', 'Parquet'])
  expect(format.element.value).toBe('csv')

  await format.setValue('parquet')
  await wrapper.setProps({ selectedSet: legacySet })

  expect(format.element.value).toBe('parquet')
  wrapper.unmount()
})
