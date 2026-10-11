import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { render } from 'vitest-browser-vue'
import { ref } from 'vue'
import { QueryClient, VueQueryPlugin } from '@tanstack/vue-query'
import { useDrawing } from '@/composables/useDrawing'
import { usePipeset } from '@/composables/usePipeset'

vi.mock(import('@/composables/usePipeset'), { spy: true })

vi.mock(import('@/composables/useDrawing'), () => ({ useDrawing: vi.fn<typeof useDrawing>() }))

const drawing = {
  isMapReady: ref(true),
  isDrawing: ref(false),
  hasBbox: ref(false),
  bbox: ref<[number, number, number, number] | null>(null),
  initializeDrawing: vi.fn<ReturnType<typeof useDrawing>['initializeDrawing']>(),
  disposeDrawing: vi.fn<ReturnType<typeof useDrawing>['disposeDrawing']>(),
  startDrawing: vi.fn<ReturnType<typeof useDrawing>['startDrawing']>(),
  resetBbox: vi.fn<ReturnType<typeof useDrawing>['resetBbox']>(),
}

let AppSidebar: (typeof import('@/components/AppSidebar.vue'))['default']
let queryClient: QueryClient

const renderSidebar = () =>
  render(AppSidebar, { global: { plugins: [[VueQueryPlugin, { queryClient }]] } })

beforeEach(async () => {
  vi.resetModules()
  AppSidebar = (await import('@/components/AppSidebar.vue')).default
  queryClient = new QueryClient()
  vi.clearAllMocks()
  drawing.isMapReady.value = true
  drawing.isDrawing.value = false
  drawing.hasBbox.value = false
  drawing.bbox.value = null
  vi.mocked(useDrawing).mockReturnValue(drawing)
})

afterEach(() => {
  for (const result of vi.mocked(usePipeset).mock.results) {
    if (result.type === 'return') result.value.pipesetId.value = undefined
  }
  queryClient.clear()
  vi.restoreAllMocks()
})

describe('AppSidebar', () => {
  it('should allow entering a pipeset name', async () => {
    const screen = await renderSidebar()
    const input = screen.getByRole('textbox', { name: 'Pipeset name' })

    await input.fill('Tokyo pipes')

    await expect.element(input).toHaveValue('Tokyo pipes')
  })

  it.each([
    { case: 'without attributes', definitions: [] },
    { case: 'with attributes', definitions: [{ name: 'active', type: 'boolean' }] },
  ])('should submit the name and selected bbox $case', async ({ definitions }) => {
    const payload = {
      name: 'Tokyo pipes',
      bbox: [139, 35, 140, 36],
      ...(definitions.length ? { attribute_definitions: definitions } : {}),
    }
    const fetch = vi
      .spyOn(globalThis, 'fetch')
      .mockResolvedValue(
        Response.json(
          { ...payload, id: 1, count: 0, status: 'pending', attribute_definitions: definitions },
          { status: 202 },
        ),
      )
    drawing.bbox.value = [139, 35, 140, 36]
    const screen = await renderSidebar()

    await screen.getByRole('textbox', { name: 'Pipeset name' }).fill('  Tokyo pipes  ')

    if (definitions.length) {
      await screen.getByRole('button', { name: 'Add attribute' }).click()
      await screen.getByRole('textbox', { name: 'Field name', exact: true }).fill('active')
      await screen.getByRole('combobox', { name: 'Field type' }).selectOptions('boolean')
    }

    await screen.getByRole('button', { name: 'Submit pipeset' }).click()

    await expect.poll(() => fetch.mock.calls.length).toBe(1)
    expect(fetch).toHaveBeenCalledWith('/pipesets', expect.objectContaining({ method: 'POST' }))
    expect(JSON.parse(fetch.mock.calls[0]![1]!.body as string)).toEqual(payload)
  })

  it('should show the generated pipe count after polling in ten seconds', async () => {
    const pipeset = {
      id: 1,
      name: 'Tokyo pipes',
      count: 25,
      bbox: [139, 35, 140, 36],
      attribute_definitions: [],
    }
    const fetch = vi
      .spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce(
        Response.json({ ...pipeset, count: 0, status: 'pending' }, { status: 202 }),
      )
      .mockResolvedValueOnce(Response.json({ ...pipeset, status: 'completed' }))
    drawing.bbox.value = [139, 35, 140, 36]
    const screen = await renderSidebar()

    await screen.getByRole('textbox', { name: 'Pipeset name' }).fill('Tokyo pipes')
    await screen.getByRole('button', { name: 'Submit pipeset' }).click()
    await expect.element(screen.getByRole('button', { name: 'Add attribute' })).toBeDisabled()
    await expect.element(screen.getByRole('textbox', { name: 'Pipeset name' })).toBeDisabled()
    await expect.element(screen.getByText('Pipe count: 25'), { timeout: 12_000 }).toBeVisible()
    await expect.element(screen.getByRole('button', { name: 'Add attribute' })).toBeEnabled()

    expect(fetch).toHaveBeenLastCalledWith(
      '/pipesets/1',
      expect.objectContaining({ method: 'GET' }),
    )
  }, 15_000)

  it('should disable drawing until the map is ready', async () => {
    drawing.isMapReady.value = false
    const screen = await renderSidebar()
    const button = screen.getByRole('button', { name: 'Start drawing' })

    await expect.element(button).toBeDisabled()
  })

  it('should start drawing when the button is clicked', async () => {
    const screen = await renderSidebar()
    const button = screen.getByRole('button', { name: 'Start drawing' })

    await button.click()

    expect(drawing.startDrawing).toHaveBeenCalledOnce()
  })

  it('should reset the existing bbox when the button is clicked', async () => {
    drawing.hasBbox.value = true
    const screen = await renderSidebar()
    const button = screen.getByRole('button', { name: 'Reset bbox' })

    await button.click()

    expect(drawing.resetBbox).toHaveBeenCalledOnce()
  })

  it('should cancel drawing when the button is clicked', async () => {
    drawing.isDrawing.value = true
    const screen = await renderSidebar()
    const button = screen.getByRole('button', { name: 'Cancel drawing' })

    await button.click()

    expect(drawing.resetBbox).toHaveBeenCalledOnce()
  })

  it('logs a generation failure and enables the form again', async () => {
    const pipeset = {
      id: 1,
      name: 'Test',
      count: 0,
      bbox: [139, 35, 140, 36],
      attribute_definitions: [],
    }
    vi.spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce(Response.json({ ...pipeset, status: 'pending' }, { status: 202 }))
      .mockResolvedValueOnce(Response.json({ ...pipeset, status: 'failed' }))
    const error = vi.spyOn(console, 'error').mockImplementation(() => {})
    drawing.bbox.value = [139, 35, 140, 36]
    const screen = await renderSidebar()
    await screen.getByRole('textbox', { name: 'Pipeset name' }).fill('Test')
    await screen.getByRole('button', { name: 'Add attribute' }).click()
    await screen.getByRole('textbox', { name: 'Field name', exact: true }).fill('active')
    await screen.getByRole('combobox', { name: 'Field type' }).selectOptions('boolean')
    await screen.getByRole('button', { name: 'Submit pipeset' }).click()
    await expect.element(screen.getByRole('button', { name: 'Add attribute' })).toBeDisabled()
    await expect.poll(() => error.mock.calls.length, { timeout: 12_000 }).toBe(1)
    expect(error).toHaveBeenCalledWith('Pipeset generation failed.', 1)
    await expect.element(screen.getByRole('button', { name: 'Add attribute' })).toBeEnabled()
    await expect
      .element(screen.getByRole('textbox', { name: 'Field name', exact: true }))
      .toHaveValue('active')
  }, 15_000)
})
