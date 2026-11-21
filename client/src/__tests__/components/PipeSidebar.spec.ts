import { flushPromises, mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'
import { defineComponent, ref } from 'vue'

import { createTestPlugins } from '@/__tests__/testSetup'
import PipeSidebar from '@/components/PipeSidebar.vue'
import { createQueryClient } from '@/queryClient'

describe('PipeSidebar', () => {
  it('should preserve the draft across keyboard tab changes and reopening', async () => {
    vi.stubGlobal('fetch', vi.fn<typeof fetch>().mockResolvedValue(Response.json([])))

    const wrapper = mount(
      defineComponent({
        components: { PipeSidebar },
        setup: () => ({ open: ref(true) }),
        template: '<PipeSidebar v-model:open="open" />',
      }),
      { global: { plugins: createTestPlugins() }, attachTo: document.body },
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
  it('should move focus across all three tabs and wrap at both ends', async () => {
    vi.stubGlobal('fetch', vi.fn<typeof fetch>().mockResolvedValue(Response.json([])))

    const wrapper = mount(PipeSidebar, {
      props: { open: true },
      global: { plugins: createTestPlugins() },
      attachTo: document.body,
    })

    try {
      const tabs = wrapper.findAll<HTMLButtonElement>('[role="tab"]')

      const [attributes, generate, exportTab] = tabs

      const steps = [
        [attributes!, 'ArrowLeft', exportTab!],
        [exportTab!, 'ArrowRight', attributes!],
        [attributes!, 'End', exportTab!],
        [exportTab!, 'ArrowLeft', generate!],
        [generate!, 'ArrowRight', exportTab!],
        [exportTab!, 'Home', attributes!],
      ] as const

      for (const [from, key, to] of steps) {
        await from.trigger('keydown', { key })
        expect(to.attributes('aria-selected')).toBe('true')
        expect(document.activeElement).toBe(to.element)
      }
    } finally {
      wrapper.unmount()
      vi.unstubAllGlobals()
    }
  })

  it('should show a newly saved attribute set when reopening the generator', async () => {
    const saved = {
      id: '4965963c-cd1c-4b2b-be38-74220dc93884',
      name: 'Water mains',
      attributes: [{ name: 'active', type: 'boolean' }],
    }

    const request = vi
      .fn<typeof fetch>()
      .mockResolvedValueOnce(Response.json([]))
      .mockResolvedValueOnce(Response.json([]))
      .mockResolvedValueOnce(Response.json(saved, { status: 201 }))
      .mockResolvedValueOnce(Response.json([saved]))
    vi.stubGlobal('fetch', request)

    const queryClient = createQueryClient()

    const defaults = queryClient.getDefaultOptions()
    queryClient.setDefaultOptions({
      ...defaults,
      queries: { ...defaults.queries, staleTime: Infinity },
    })

    const wrapper = mount(PipeSidebar, {
      global: { plugins: createTestPlugins(queryClient) },
      props: { open: true },
    })

    try {
      const [attributes, generate] = wrapper.findAll('[role="tab"]')

      const panel = wrapper.get('[role="tabpanel"][id$="-generate"]')
      await generate!.trigger('click')
      await vi.waitFor(() => expect(panel.text()).toContain('Create an attribute set'))
      await attributes!.trigger('click')

      const editor = wrapper.get('[role="tabpanel"][id$="-attributes"]')
      await editor.get('input').setValue(saved.name)
      await editor.get('fieldset fieldset input').setValue('active')
      await editor.get('select').setValue('boolean')
      await editor.get('form').trigger('submit')
      await vi.waitFor(() => expect(editor.text()).toContain('Attribute set saved.'))

      await generate!.trigger('click')
      await vi.waitFor(() => expect(panel.get('select').text()).toContain(saved.name))
    } finally {
      wrapper.unmount()
      vi.unstubAllGlobals()
    }
  })
})
