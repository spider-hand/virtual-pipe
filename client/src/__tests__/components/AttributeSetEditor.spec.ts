import { mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'

import AttributeSetEditor from '@/components/AttributeSetEditor.vue'

describe('AttributeSetEditor', () => {
  it('should render the default state', () => {
    const wrapper = mount(AttributeSetEditor)

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
    expect(wrapper.get('button:disabled').text()).toBe('Save Attribute Set')
  })

  it('should add and delete attributes while keeping other edits', async () => {
    const wrapper = mount(AttributeSetEditor)
    await wrapper.get('fieldset input').setValue('material')
    await wrapper.get('button.add').trigger('click')
    await wrapper.findAll('fieldset')[1]!.get('input').setValue('diameter_mm')

    await wrapper.get('button[aria-label="Delete attribute 1"]').trigger('click')
    expect(wrapper.get('fieldset input').element.value).toBe('diameter_mm')

    await wrapper.get('button[aria-label="Delete attribute 1"]').trigger('click')
    expect(wrapper.findAll('fieldset')).toHaveLength(0)
    expect(wrapper.get('button.add').isVisible()).toBe(true)
  })

  it('should flag a blank field name on blur', async () => {
    const wrapper = mount(AttributeSetEditor)
    const name = wrapper.get('fieldset input')
    await name.trigger('blur')
    await vi.waitFor(() => expect(name.attributes('aria-invalid')).toBe('true'))
  })

  it('should flag both duplicate field names after trimming', async () => {
    const wrapper = mount(AttributeSetEditor)
    const name = wrapper.get('fieldset input')
    await name.setValue('material')
    await wrapper.get('button.add').trigger('click')
    const second = wrapper.findAll('fieldset')[1]!.get('input')
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
    const wrapper = mount(AttributeSetEditor)
    await wrapper.get('fieldset input').setValue('material')
    await wrapper.get('button.add').trigger('click')
    const remaining = wrapper.findAll('fieldset')[1]!.get('input')
    await remaining.setValue('material')

    await vi.waitFor(() => expect(remaining.attributes('aria-invalid')).toBe('true'))

    await wrapper.get('button[aria-label="Delete attribute 1"]').trigger('click')
    await vi.waitFor(() => expect(remaining.attributes('aria-invalid')).toBeUndefined())
    expect(remaining.element.value).toBe('material')
  })

  it.each(['管径', 'Diameter', 'pipe diameter', 'pipe-diameter', '2inch'])(
    'should show a field-name error for %s until corrected',
    async (value) => {
      const wrapper = mount(AttributeSetEditor)
      const name = wrapper.get('fieldset input')
      await name.setValue(value)
      expect(name.element.value).toBe(value)
      await vi.waitFor(() => expect(name.attributes('aria-invalid')).toBe('true'))

      await name.setValue('diameter_mm')
      await vi.waitFor(() => expect(name.attributes('aria-invalid')).toBeUndefined())
    },
  )

  it('should accept Japanese text in the set name and string choices', async () => {
    const wrapper = mount(AttributeSetEditor)
    const setName = wrapper.get('input')
    const choices = wrapper.get('fieldset > label input')
    await setName.setValue('配水管')
    await setName.trigger('blur')
    await choices.setValue('鋼, 塩化ビニル')
    await choices.trigger('blur')

    expect(setName.attributes('aria-invalid')).toBeUndefined()
    expect(choices.attributes('aria-invalid')).toBeUndefined()
  })

  it('should default to Sequential and reset the ID format after changing type', async () => {
    const wrapper = mount(AttributeSetEditor)
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
    const wrapper = mount(AttributeSetEditor)
    const getChoices = () => wrapper.get('fieldset > label input')
    await getChoices().setValue(' AC, PVC,')
    await getChoices().trigger('blur')
    expect(getChoices().attributes('aria-invalid')).toBeUndefined()

    await wrapper.get('select').setValue('boolean')
    expect(wrapper.findAll('fieldset input')).toHaveLength(1)
    await wrapper.get('select').setValue('string')
    expect(getChoices().element.value).toBe('')
  })

  it('should require at least one string choice', async () => {
    const wrapper = mount(AttributeSetEditor)
    const choices = wrapper.get('fieldset > label input')
    await choices.setValue(', ,')
    await choices.trigger('blur')

    await vi.waitFor(() => expect(choices.attributes('aria-invalid')).toBe('true'))
  })

  it.each([
    ['integer', '2', '1'],
    ['decimal', '1.00000000000000000002', '1.00000000000000000001'],
    ['date', '2025-02-02', '2025-02-01'],
  ])('should reject reversed %s bounds', async (type, high, low) => {
    const wrapper = mount(AttributeSetEditor)
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
    const wrapper = mount(AttributeSetEditor)
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
    const wrapper = mount(AttributeSetEditor)
    await wrapper.get('select').setValue(type)
    const [min, max] = wrapper.findAll('input[type="text"]')
    await min!.setValue(lower)
    await max!.setValue(upper)

    await vi.waitFor(() => expect(wrapper.text()).toContain(message))
  })

  it('should preserve typed decimal bounds and clear the precision error after correction', async () => {
    const wrapper = mount(AttributeSetEditor)
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
