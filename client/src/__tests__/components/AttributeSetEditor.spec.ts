import { mount } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'

import AttributeSetEditor from '@/components/AttributeSetEditor.vue'
import { createAppI18n } from '@/i18n'

const global = { plugins: [createAppI18n('en')] }

describe('AttributeSetEditor', () => {
  afterEach(() => vi.unstubAllGlobals())

  it('should validate untouched fields before requesting a save', async () => {
    const request = vi.fn<typeof fetch>()
    vi.stubGlobal('fetch', request)
    const wrapper = mount(AttributeSetEditor, { global })
    await wrapper.get('form').trigger('submit')

    await vi.waitFor(() => {
      expect(wrapper.findAll('[aria-invalid="true"]')).toHaveLength(3)
      expect(wrapper.get('button[type=submit]').element.disabled).toBe(false)
    })
    expect(request).not.toHaveBeenCalled()
  })

  it('should save typed attributes once and start a fresh draft on request', async () => {
    let respond!: (response: Response) => void
    const request = vi.fn<typeof fetch>(() => new Promise((resolve) => (respond = resolve)))
    vi.stubGlobal('fetch', request)
    const wrapper = mount(AttributeSetEditor, { global })
    await wrapper.get('input').setValue(' Mains ')
    const name = wrapper.get('fieldset fieldset input')
    await name.setValue(' pressure ')
    await wrapper.get('select').setValue('decimal')
    const [min, max] = wrapper.findAll('input[type="text"]')
    await min!.setValue('1.20')
    await max!.setValue('2.00')

    await wrapper.get('button.add').trigger('click')
    const id = wrapper.findAll('fieldset fieldset')[1]!
    await id.get('input').setValue('pipe_id')
    await id.get('select').setValue('id')
    await id.findAll('select')[1]!.setValue('uuid')

    await wrapper.get('form').trigger('submit')
    await vi.waitFor(() => expect(request).toHaveBeenCalledOnce())
    expect(wrapper.get('button[type=submit]').element.disabled).toBe(true)
    await wrapper.get('form').trigger('submit')
    expect(request).toHaveBeenCalledOnce()

    const payload = {
      name: 'Mains',
      attributes: [
        { name: 'pressure', type: 'decimal', min: '1.20', max: '2.00' },
        { name: 'pipe_id', type: 'id', id_format: 'uuid' },
      ],
    }
    const [url, options] = request.mock.calls[0]!
    expect(url).toBe('/api/attribute-sets/')
    expect(options?.method).toBe('POST')
    expect(JSON.parse(options?.body as string)).toEqual(payload)
    respond(
      Response.json({ id: '4965963c-cd1c-4b2b-be38-74220dc93884', ...payload }, { status: 201 }),
    )

    await vi.waitFor(() => expect(wrapper.get('[role=status]').text()).toBe('Attribute set saved.'))
    expect(wrapper.get('input').element.value.trim()).toBe('Mains')
    expect(wrapper.get('input').element.matches(':disabled')).toBe(false)

    await wrapper.get('footer button').trigger('click')
    expect(wrapper.get('input').element.value).toBe('')
    expect(wrapper.get('select').element.value).toBe('string')
    expect(wrapper.findAll('fieldset fieldset')).toHaveLength(1)
  })

  it('should let users revise a saved draft and save the revision as a new attribute set', async () => {
    const request = vi
      .fn<typeof fetch>()
      .mockImplementation(async (_url, options) =>
        Response.json({ id: 'saved-id', ...JSON.parse(String(options?.body)) }, { status: 201 }),
      )
    vi.stubGlobal('fetch', request)
    const wrapper = mount(AttributeSetEditor, { global })
    const name = wrapper.get('input')
    await name.setValue('Mains')
    await wrapper.get('fieldset fieldset input').setValue('active')
    await wrapper.get('select').setValue('boolean')
    await wrapper.get('form').trigger('submit')
    await vi.waitFor(() => expect(wrapper.get('[role=status]').text()).toBe('Attribute set saved.'))

    expect(name.element.matches(':disabled')).toBe(false)
    await name.setValue('Mains revision')
    expect(wrapper.get('button[type=submit]').text()).toBe('Save Attribute Set')

    await wrapper.get('form').trigger('submit')
    await vi.waitFor(() => expect(request).toHaveBeenCalledTimes(2))
    expect(request).toHaveBeenLastCalledWith(
      '/api/attribute-sets/',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({
          name: 'Mains revision',
          attributes: [{ name: 'active', type: 'boolean' }],
        }),
      }),
    )
  })

  it('should retain the editable draft when the save request fails', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn<typeof fetch>().mockResolvedValue(Response.json({}, { status: 400 })),
    )
    const wrapper = mount(AttributeSetEditor, { global })
    await wrapper.get('input').setValue('Mains')
    await wrapper.get('fieldset fieldset input').setValue('active')
    await wrapper.get('select').setValue('boolean')
    await wrapper.get('form').trigger('submit')

    await vi.waitFor(() => expect(wrapper.get('[role=alert]').text()).toContain('Could not save'))
    expect(wrapper.get('input').element.value).toBe('Mains')
    expect(wrapper.get('input').element.matches(':disabled')).toBe(false)
    expect(wrapper.get('select').element.value).toBe('boolean')
    expect(wrapper.get('button[type=submit]').element.disabled).toBe(false)
  })

  it('should render the default state', () => {
    const wrapper = mount(AttributeSetEditor, { global })

    expect(wrapper.get('input').element.value).toBe('')
    expect(wrapper.get('select').element.value).toBe('string')
    expect(wrapper.findAll('option').map((option) => option.element.value)).toEqual([
      'string',
      'integer',
      'decimal',
      'boolean',
      'date',
      'id',
    ])
    expect(wrapper.get('button[type=submit]').text()).toBe('Save Attribute Set')
  })

  it('should add and delete attributes while keeping other edits', async () => {
    const wrapper = mount(AttributeSetEditor, { global })
    await wrapper.get('fieldset fieldset input').setValue('material')
    await wrapper.get('button.add').trigger('click')
    await wrapper.findAll('fieldset fieldset')[1]!.get('input').setValue('diameter_mm')

    await wrapper.get('button[aria-label="Delete attribute 1"]').trigger('click')
    expect(wrapper.get('fieldset fieldset input').element.value).toBe('diameter_mm')

    await wrapper.get('button[aria-label="Delete attribute 1"]').trigger('click')
    expect(wrapper.findAll('fieldset fieldset')).toHaveLength(0)
    expect(wrapper.get('button.add').isVisible()).toBe(true)
  })

  it('should flag a blank field name on blur', async () => {
    const wrapper = mount(AttributeSetEditor, { global })
    const name = wrapper.get('fieldset fieldset input')
    await name.trigger('blur')
    await vi.waitFor(() => expect(name.attributes('aria-invalid')).toBe('true'))
  })

  it('should flag both duplicate field names after trimming', async () => {
    const wrapper = mount(AttributeSetEditor, { global })
    const name = wrapper.get('fieldset fieldset input')
    await name.setValue('material')
    await wrapper.get('button.add').trigger('click')
    const second = wrapper.findAll('fieldset fieldset')[1]!.get('input')
    await second.setValue(' material ')
    await vi.waitFor(() => expect(name.attributes('aria-invalid')).toBe('true'))
    await vi.waitFor(() => expect(second.attributes('aria-invalid')).toBe('true'))

    await second.setValue(' diameter_mm ')
    await vi.waitFor(() => {
      expect(name.attributes('aria-invalid')).toBeUndefined()
      expect(second.attributes('aria-invalid')).toBeUndefined()
    })
  })

  it('should clear a duplicate error when the other field is deleted', async () => {
    const wrapper = mount(AttributeSetEditor, { global })
    await wrapper.get('fieldset fieldset input').setValue('material')
    await wrapper.get('button.add').trigger('click')
    const remaining = wrapper.findAll('fieldset fieldset')[1]!.get('input')
    await remaining.setValue('material')

    await vi.waitFor(() => expect(remaining.attributes('aria-invalid')).toBe('true'))

    await wrapper.get('button[aria-label="Delete attribute 1"]').trigger('click')
    await vi.waitFor(() => expect(remaining.attributes('aria-invalid')).toBeUndefined())
    expect(remaining.element.value).toBe('material')
  })

  it.each(['管径', 'Diameter', 'pipe diameter', 'pipe-diameter', '2inch'])(
    'should show a field-name error for %s until corrected',
    async (value) => {
      const wrapper = mount(AttributeSetEditor, { global })
      const name = wrapper.get('fieldset fieldset input')
      await name.setValue(value)
      expect(name.element.value).toBe(value)
      await vi.waitFor(() => expect(name.attributes('aria-invalid')).toBe('true'))

      await name.setValue('diameter_mm')
      await vi.waitFor(() => expect(name.attributes('aria-invalid')).toBeUndefined())
    },
  )

  it('should accept Japanese text in the set name and string choices', async () => {
    const wrapper = mount(AttributeSetEditor, { global })
    const setName = wrapper.get('input')
    const choices = wrapper.get('fieldset fieldset > label input')
    await setName.setValue('配水管')
    await setName.trigger('blur')
    await choices.setValue('鋼, 塩化ビニル')
    await choices.trigger('blur')

    expect(setName.attributes('aria-invalid')).toBeUndefined()
    expect(choices.attributes('aria-invalid')).toBeUndefined()
  })

  it('should default to Sequential and reset the ID format after changing type', async () => {
    const wrapper = mount(AttributeSetEditor, { global })
    const type = wrapper.get('select')
    await type.setValue('id')
    const format = () => wrapper.findAll('select')[1]!

    expect(format().element.value).toBe('sequential')
    expect(wrapper.text()).toContain('PIPE-000001')

    await format().setValue('uuid')
    expect(format().element.value).toBe('uuid')
    expect(wrapper.text()).not.toContain('PIPE-000001')

    await type.setValue('boolean')
    expect(wrapper.findAll('select')).toHaveLength(1)
    await type.setValue('id')
    expect(format().element.value).toBe('sequential')
  })

  it('should accept trailing commas and clear choices when the type changes', async () => {
    const wrapper = mount(AttributeSetEditor, { global })
    const getChoices = () => wrapper.get('fieldset fieldset > label input')
    await getChoices().setValue(' AC, PVC,')
    await getChoices().trigger('blur')
    expect(getChoices().attributes('aria-invalid')).toBeUndefined()

    await wrapper.get('select').setValue('boolean')
    expect(wrapper.findAll('fieldset fieldset input')).toHaveLength(1)
    await wrapper.get('select').setValue('string')
    expect(getChoices().element.value).toBe('')
  })

  it('should require at least one string choice', async () => {
    const wrapper = mount(AttributeSetEditor, { global })
    const choices = wrapper.get('fieldset fieldset > label input')
    await choices.setValue(', ,')
    await choices.trigger('blur')

    await vi.waitFor(() => expect(choices.attributes('aria-invalid')).toBe('true'))
  })

  it.each([
    ['integer', '2', '1'],
    ['decimal', '1.00000000000000000002', '1.00000000000000000001'],
    ['date', '2025-02-02', '2025-02-01'],
  ])('should reject reversed %s bounds', async (type, high, low) => {
    const wrapper = mount(AttributeSetEditor, { global })
    await wrapper.get('select').setValue(type)
    const [min, max] = wrapper.findAll(`input[type="${type === 'date' ? 'date' : 'text'}"]`)
    await min!.setValue(high)
    await max!.setValue(low)
    await max!.trigger('blur')
    await vi.waitFor(() => expect(max!.attributes('aria-invalid')).toBe('true'))
    expect(wrapper.text()).toContain('The maximum must be at least the minimum.')
  })

  it.each([
    ['integer', '-2'],
    ['decimal', '2.00'],
    ['date', '2025-02-02'],
  ])('should accept equal %s bounds for a fixed value', async (type, value) => {
    const wrapper = mount(AttributeSetEditor, { global })
    await wrapper.get('select').setValue(type)
    const [min, max] = wrapper.findAll(`input[type="${type === 'date' ? 'date' : 'text'}"]`)
    await min!.setValue(value)
    await max!.setValue(value)
    await max!.trigger('blur')

    expect(max!.attributes('aria-invalid')).toBeUndefined()
  })

  it.each([
    ['integer', '1.00', '10', 'Enter whole numbers for both bounds.'],
    ['decimal', '1', '10.00', 'Enter at least one decimal place in both bounds.'],
  ])('should reject invalid %s bounds', async (type, lower, upper, message) => {
    const wrapper = mount(AttributeSetEditor, { global })
    await wrapper.get('select').setValue(type)
    const [min, max] = wrapper.findAll('input[type="text"]')
    await min!.setValue(lower)
    await max!.setValue(upper)

    await vi.waitFor(() => expect(wrapper.text()).toContain(message))
  })

  it('should preserve typed decimal bounds and clear the precision error after correction', async () => {
    const wrapper = mount(AttributeSetEditor, { global })
    await wrapper.get('select').setValue('decimal')
    const [min, max] = wrapper.findAll('input[type="text"]')
    await min!.setValue('1.00')
    await max!.setValue('10.00000')

    await vi.waitFor(() => {
      expect(wrapper.text()).toContain('Use the same number of decimal places')
      expect(min!.attributes('aria-invalid')).toBe('true')
      expect(max!.attributes('aria-invalid')).toBe('true')
    })
    expect(min!.element.value).toBe('1.00')
    expect(max!.element.value).toBe('10.00000')

    await min!.setValue('1.00000')
    await vi.waitFor(() => expect(max!.attributes('aria-invalid')).toBeUndefined())
  })
})
