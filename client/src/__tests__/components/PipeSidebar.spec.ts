import { flushPromises, mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'
import { defineComponent, ref } from 'vue'

import PipeSidebar from '@/components/PipeSidebar.vue'

describe('PipeSidebar', () => {
  it('should preserve the draft across keyboard tab changes and reopening', async () => {
    vi.stubGlobal('fetch', vi.fn<typeof fetch>().mockResolvedValue(Response.json([])))
    const wrapper = mount(
      defineComponent({
        components: { PipeSidebar },
        setup: () => ({ open: ref(true) }),
        template: '<PipeSidebar v-model:open="open" />',
      }),
      { attachTo: document.body },
    )
    const [attributes, generate] = wrapper.findAll('[role="tab"]')
    const name = wrapper.get('[role="tabpanel"][id$="-attributes"] input')

    try {
      await name.setValue('Water mains')
      await attributes!.trigger('keydown', { key: 'ArrowRight' })
      await flushPromises()
      expect(generate!.attributes('aria-selected')).toBe('true')
      expect(document.activeElement).toBe(generate!.element)

      await generate!.trigger('keydown', { key: 'Home' })
      expect(name.isVisible()).toBe(true)
      expect(name.element.value).toBe('Water mains')

      await wrapper.get('button[aria-label="Close pipe tools"]').trigger('click')
      const launcher = wrapper.get('button[aria-label="Open pipe tools"]')
      expect(name.isVisible()).toBe(false)
      expect(document.activeElement).toBe(launcher.element)

      await launcher.trigger('click')
      expect(name.isVisible()).toBe(true)
      expect(name.element.value).toBe('Water mains')
      expect(document.activeElement).toBe(attributes!.element)
    } finally {
      wrapper.unmount()
      vi.unstubAllGlobals()
    }
  })
})
