import { describe, expect, it } from 'vitest'
import { render } from 'vitest-browser-vue'
import { defineComponent, h, ref } from 'vue'
import AttributeForm from '@/components/AttributeForm.vue'

const renderForm = async () => {
  const form = ref<InstanceType<typeof AttributeForm> | null>(null)
  const screen = await render(
    defineComponent({ setup: () => () => h(AttributeForm, { ref: form }) }),
  )

  return { screen, getDefinitions: () => form.value!.getDefinitions() }
}

const addField = async (
  screen: Awaited<ReturnType<typeof renderForm>>['screen'],
  name: string,
  type: string,
) => {
  await screen.getByRole('button', { name: 'Add attribute' }).click()
  const index = screen.getByRole('textbox', { name: 'Field name', exact: true }).all().length - 1

  await screen.getByRole('textbox', { name: 'Field name', exact: true }).nth(index).fill(name)
  await screen.getByRole('combobox', { name: 'Field type' }).nth(index).selectOptions(type)
}

describe('AttributeForm', () => {
  it('returns no definitions when no attributes are configured', async () => {
    const { getDefinitions } = await renderForm()

    expect(getDefinitions()).toEqual([])
  })

  it('returns all types with trimmed names and normalized category options', async () => {
    const { screen, getDefinitions } = await renderForm()

    await addField(screen, ' label ', 'string')
    await screen.getByRole('spinbutton', { name: 'Minimum length' }).fill('3')
    await screen.getByRole('spinbutton', { name: 'Maximum length' }).fill('8')

    await addField(screen, 'diameter', 'number')
    await screen.getByRole('spinbutton', { name: 'Minimum value' }).fill('-10')
    await screen.getByRole('spinbutton', { name: 'Maximum value' }).fill('20')

    await addField(screen, 'active', 'boolean')
    await addField(screen, 'material', 'category')
    await screen
      .getByRole('textbox', {
        name: 'Categories (comma-separated; commas cannot be part of a category)',
      })
      .fill(' PVC , ,steel,PVC ')

    await expect.element(screen.getByText('Options: PVC, steel')).toBeVisible()
    expect(getDefinitions()).toEqual([
      { name: 'label', type: 'string', min: 3, max: 8 },
      { name: 'diameter', type: 'number', min: -10, max: 20 },
      { name: 'active', type: 'boolean' },
      { name: 'material', type: 'category', categories: ['PVC', 'steel'] },
    ])
  })

  it('removes fields and preserves inputs when switching types', async () => {
    const { screen, getDefinitions } = await renderForm()

    await addField(screen, 'value', 'number')
    await screen.getByRole('spinbutton', { name: 'Minimum value' }).fill('2')
    await screen.getByRole('spinbutton', { name: 'Maximum value' }).fill('5')
    await screen.getByRole('combobox', { name: 'Field type' }).selectOptions('boolean')

    expect(screen.getByRole('spinbutton').all()).toHaveLength(0)
    expect(getDefinitions()).toEqual([{ name: 'value', type: 'boolean' }])

    await screen.getByRole('combobox', { name: 'Field type' }).selectOptions('number')
    await expect.element(screen.getByRole('spinbutton', { name: 'Minimum value' })).toHaveValue(2)
    await expect.element(screen.getByRole('spinbutton', { name: 'Maximum value' })).toHaveValue(5)
    await screen.getByRole('button', { name: 'Remove attribute' }).click()

    expect(screen.getByRole('combobox', { name: 'Field type' }).all()).toHaveLength(0)
    expect(getDefinitions()).toEqual([])
  })

  it.each([
    ['reserved name', 'id', 'boolean', '', '', 'Attribute names'],
    ['empty name', '', 'boolean', '', '', 'Attribute names'],
    ['negative string length', 'length', 'string', '-1', '10', 'Invalid minimum or maximum'],
    ['reversed string range', 'length', 'string', '10', '2', 'Invalid minimum or maximum'],
    ['fractional number bound', 'count', 'number', '0.5', '10', 'Invalid minimum or maximum'],
    ['missing number bound', 'count', 'number', '', '10', 'Invalid minimum or maximum'],
    ['empty categories', 'material', 'category', '', '', 'At least one category'],
  ])('rejects %s', async (_reason, name, type, min, max, message) => {
    const { screen, getDefinitions } = await renderForm()

    await addField(screen, name, type)
    if (type === 'string' || type === 'number') {
      await screen.getByRole('spinbutton').nth(0).fill(min)
      await screen.getByRole('spinbutton').nth(1).fill(max)
    }

    expect(getDefinitions).toThrow(message)
  })

  it('rejects duplicate names after trimming', async () => {
    const { screen, getDefinitions } = await renderForm()

    await addField(screen, 'active', 'boolean')
    await addField(screen, ' active ', 'boolean')

    expect(getDefinitions).toThrow('Attribute names')
  })
})
