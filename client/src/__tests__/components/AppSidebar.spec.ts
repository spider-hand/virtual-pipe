import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { enableAutoUnmount, mount } from '@vue/test-utils'
import { ref } from 'vue'
import AppSidebar from '@/components/AppSidebar.vue'
import { useDrawing } from '@/composables/useDrawing'

vi.mock('@/composables/useDrawing', () => ({ useDrawing: vi.fn<typeof useDrawing>() }))

enableAutoUnmount(afterEach)

const drawing = {
  isMapReady: ref(true),
  isDrawing: ref(false),
  hasBbox: ref(false),
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
  it('should disable drawing until the map is ready', async () => {
    drawing.isMapReady.value = false
    const wrapper = mount(AppSidebar)
    const button = wrapper.get('button')

    expect(button.element.disabled).toBe(true)
    await button.trigger('click')

    expect(drawing.startDrawing).not.toHaveBeenCalled()
    expect(drawing.resetBbox).not.toHaveBeenCalled()
  })

  it('should start drawing when the button is clicked', async () => {
    const wrapper = mount(AppSidebar)
    const button = wrapper.get('button')

    expect(button.text()).toBe('Start drawing')
    expect(button.element.disabled).toBe(false)
    await button.trigger('click')

    expect(drawing.startDrawing).toHaveBeenCalledOnce()
    expect(drawing.resetBbox).not.toHaveBeenCalled()
  })

  it('should reset the existing bbox when the button is clicked', async () => {
    drawing.hasBbox.value = true
    const wrapper = mount(AppSidebar)
    const button = wrapper.get('button')

    expect(button.text()).toBe('Reset bbox')
    await button.trigger('click')

    expect(drawing.resetBbox).toHaveBeenCalledOnce()
    expect(drawing.startDrawing).not.toHaveBeenCalled()
  })

  it('should cancel drawing when the button is clicked', async () => {
    drawing.isDrawing.value = true
    const wrapper = mount(AppSidebar)
    const button = wrapper.get('button')

    expect(button.text()).toBe('Cancel drawing')
    await button.trigger('click')

    expect(drawing.resetBbox).toHaveBeenCalledOnce()
    expect(drawing.startDrawing).not.toHaveBeenCalled()
  })
})
