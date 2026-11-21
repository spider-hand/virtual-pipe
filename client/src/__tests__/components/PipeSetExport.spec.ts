import { mount } from '@vue/test-utils'
import { afterEach, expect, it, vi } from 'vitest'

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

afterEach(() => {
  vi.restoreAllMocks()
  vi.unstubAllGlobals()
})

const observeDownload = () => {
  const downloaded = vi.fn<(filename: string) => void>()
  vi.stubGlobal(
    'URL',
    class extends URL {
      static createObjectURL = () => 'blob:pipe-set'
      static revokeObjectURL = () => undefined
    },
  )
  vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(function (
    this: HTMLAnchorElement,
  ) {
    downloaded(this.download)
  })
  return downloaded
}

it('should render the default state', () => {
  const wrapper = mount(PipeSetExport, { global: { plugins: createTestPlugins() } })

  expect(wrapper.text()).toContain('Select a pipe set to preview its attributes.')
  expect(wrapper.get('select').element.disabled).toBe(true)
  expect(wrapper.get('button').element.disabled).toBe(true)
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

it('should download the selected format using the server filename', async () => {
  let respond!: (response: Response) => void

  const request = vi.fn<typeof fetch>(() => new Promise((resolve) => (respond = resolve)))
  vi.stubGlobal('fetch', request)

  const downloaded = observeDownload()

  const wrapper = mount(PipeSetExport, {
    props: { selectedSet },
    global: { plugins: createTestPlugins() },
  })

  const button = wrapper.get('button')

  await wrapper.get('select').setValue('parquet')
  await button.trigger('click')
  await vi.waitFor(() => expect(request).toHaveBeenCalledOnce())
  expect(request).toHaveBeenCalledWith(
    '/api/pipesets/mains/export/?file_format=parquet',
    expect.objectContaining({ method: 'GET' }),
  )
  expect(button.element.disabled).toBe(true)
  expect(wrapper.get('[role=status]').text()).toBe('Preparing download…')
  await button.trigger('click')
  expect(request).toHaveBeenCalledOnce()

  await wrapper.setProps({ selectedSet: legacySet })
  respond(
    new Response('PAR1', {
      headers: {
        'Content-Disposition': "attachment; filename*=UTF-8''%E6%9D%B1%E4%BA%AC%20mains.parquet",
      },
    }),
  )

  await vi.waitFor(() => expect(downloaded).toHaveBeenCalledWith('東京 mains.parquet'))
  expect(button.element.disabled).toBe(false)
  wrapper.unmount()
})

it('should let users retry a failed download', async () => {
  const request = vi
    .fn<typeof fetch>()
    .mockResolvedValueOnce(Response.json({}, { status: 500 }))
    .mockResolvedValueOnce(
      new Response('geometry', {
        headers: { 'Content-Disposition': 'attachment; filename="Demo mains.csv"' },
      }),
    )
  vi.stubGlobal('fetch', request)

  const downloaded = observeDownload()

  const wrapper = mount(PipeSetExport, {
    props: { selectedSet },
    global: { plugins: createTestPlugins() },
  })

  const button = wrapper.get('button')

  await button.trigger('click')
  await vi.waitFor(() => expect(wrapper.get('[role=alert]').text()).toContain('Could not export'))
  expect(button.element.disabled).toBe(false)

  await button.trigger('click')
  await vi.waitFor(() => expect(downloaded).toHaveBeenCalledWith('Demo mains.csv'))
  expect(wrapper.find('[role=alert]').exists()).toBe(false)
  wrapper.unmount()
})
