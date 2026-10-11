import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { render } from 'vitest-browser-vue'
import { ref } from 'vue'
import { QueryClient, VueQueryPlugin } from '@tanstack/vue-query'
import { useDrawing } from '@/composables/useDrawing'

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

  it('should submit the name and selected bbox', async () => {
    const payload = { name: 'Tokyo pipes', bbox: [139, 35, 140, 36] }
    const fetch = vi
      .spyOn(globalThis, 'fetch')
      .mockResolvedValue(
        Response.json({ ...payload, id: 1, count: 0, status: 'pending' }, { status: 202 }),
      )
    drawing.bbox.value = [139, 35, 140, 36]
    const screen = await renderSidebar()

    await screen.getByRole('textbox', { name: 'Pipeset name' }).fill('  Tokyo pipes  ')
    await screen.getByRole('button', { name: 'Submit pipeset' }).click()

    await expect.poll(() => fetch.mock.calls.length).toBe(1)
    expect(fetch).toHaveBeenCalledWith(
      '/pipesets',
      expect.objectContaining({ method: 'POST', body: JSON.stringify(payload) }),
    )
  })

  it('should show the generated pipe count after polling in ten seconds', async () => {
    const pipeset = { id: 1, name: 'Tokyo pipes', count: 25, bbox: [139, 35, 140, 36] }
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
    await expect.element(screen.getByText('Pipe count: 25'), { timeout: 12_000 }).toBeVisible()

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
})
