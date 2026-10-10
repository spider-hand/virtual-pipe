import { beforeEach, describe, expect, it, vi } from 'vitest'
import { render } from 'vitest-browser-vue'
import { ref } from 'vue'
import AppSidebar from '@/components/AppSidebar.vue'
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

beforeEach(() => {
  vi.clearAllMocks()
  drawing.isMapReady.value = true
  drawing.isDrawing.value = false
  drawing.hasBbox.value = false
  vi.mocked(useDrawing).mockReturnValue(drawing)
})

describe('AppSidebar', () => {
  it('should allow entering a pipeset name', async () => {
    const screen = await render(AppSidebar)
    const input = screen.getByRole('textbox', { name: 'Pipeset name' })

    await input.fill('Tokyo pipes')

    await expect.element(input).toHaveValue('Tokyo pipes')
  })

  it('should default the pipe count to one', async () => {
    const screen = await render(AppSidebar)

    await expect.element(screen.getByRole('spinbutton', { name: 'Pipe count' })).toHaveValue(1)
  })

  it('should allow entering a pipe count', async () => {
    const screen = await render(AppSidebar)
    const input = screen.getByRole('spinbutton', { name: 'Pipe count' })

    await input.fill('25')

    await expect.element(input).toHaveValue(25)
  })

  it('should disable drawing until the map is ready', async () => {
    drawing.isMapReady.value = false
    const screen = await render(AppSidebar)
    const button = screen.getByRole('button', { name: 'Start drawing' })

    await expect.element(button).toBeDisabled()

    expect(drawing.startDrawing).not.toHaveBeenCalled()
    expect(drawing.resetBbox).not.toHaveBeenCalled()
  })

  it('should start drawing when the button is clicked', async () => {
    const screen = await render(AppSidebar)
    const button = screen.getByRole('button', { name: 'Start drawing' })

    await expect.element(button).toBeEnabled()
    await button.click()

    expect(drawing.startDrawing).toHaveBeenCalledOnce()
    expect(drawing.resetBbox).not.toHaveBeenCalled()
  })

  it('should reset the existing bbox when the button is clicked', async () => {
    drawing.hasBbox.value = true
    const screen = await render(AppSidebar)
    const button = screen.getByRole('button', { name: 'Reset bbox' })

    await button.click()

    expect(drawing.resetBbox).toHaveBeenCalledOnce()
    expect(drawing.startDrawing).not.toHaveBeenCalled()
  })

  it('should cancel drawing when the button is clicked', async () => {
    drawing.isDrawing.value = true
    const screen = await render(AppSidebar)
    const button = screen.getByRole('button', { name: 'Cancel drawing' })

    await button.click()

    expect(drawing.resetBbox).toHaveBeenCalledOnce()
    expect(drawing.startDrawing).not.toHaveBeenCalled()
  })
})
