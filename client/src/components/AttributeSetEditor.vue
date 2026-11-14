<script setup lang="ts">
import { ChevronDown, Plus, Trash2 } from '@lucide/vue'
import { useFieldArray, useForm } from 'vee-validate'
import { nextTick, useId, useTemplateRef, watch } from 'vue'

import en from '@/locales/en.json'
import ja from '@/locales/ja.json'

const locale = navigator.language.toLowerCase().startsWith('ja') ? ja : en
const messages = locale.components.AttributeSetEditor
const types = ['string', 'integer', 'decimal', 'boolean', 'date', 'id'] as const
const idFormats = ['sequential', 'uuid'] as const
const id = useId()
const editor = useTemplateRef<HTMLDivElement>('editor')

const emptyDetails = () => ({
  choices: '',
  min: '',
  max: '',
  idFormat: 'sequential' as (typeof idFormats)[number],
  touched: false,
})

const createRow = () => ({
  name: '',
  nameTouched: false,
  type: 'string' as (typeof types)[number],
  details: emptyDetails(),
})

type Row = ReturnType<typeof createRow>
type Draft = { setName: string; setNameTouched: boolean; rows: Row[] }

const nameRule = (rows: Row[], row: Row, index: number) => {
  const name = row.name.trim()
  if (!name) return row.nameTouched ? messages.nameRequired : true
  if (rows.some((other, otherIndex) => otherIndex !== index && other.name.trim() === name)) {
    return messages.duplicateName
  }
  return /^[a-z][a-z0-9_]*$/.test(name) || messages.invalidName
}

const parseChoices = (text: string) =>
  text
    .split(',')
    .map((choice) => choice.trim())
    .filter(Boolean)

const detailsRule = (row: Row) => {
  const { choices, min, max, touched } = row.details
  if (row.type === 'boolean' || row.type === 'id') return true

  if (row.type === 'string') {
    return !touched || parseChoices(choices).length > 0 || messages.choicesRequired
  }

  if (!min.trim() || !max.trim()) return !touched || messages.boundsRequired
  if (row.type === 'date' && !touched) return true

  if (row.type === 'date') {
    const lower = Date.parse(min)
    const upper = Date.parse(max)
    if (!Number.isFinite(lower) || !Number.isFinite(upper)) return messages.boundsRequired
    return lower <= upper || messages.reversedRange
  }

  const lower = min.trim()
  const upper = max.trim()

  if (row.type === 'integer') {
    const integer = /^-?[0-9]+$/
    if (!integer.test(lower) || !integer.test(upper)) return messages.integerBounds
  } else {
    const decimal = /^-?[0-9]+[.]([0-9]+)$/
    const lowerFraction = lower.match(decimal)?.[1]
    const upperFraction = upper.match(decimal)?.[1]
    if (!lowerFraction || !upperFraction) return messages.decimalBounds
    if (lowerFraction.length !== upperFraction.length) return messages.decimalPrecision
  }

  // Compare the bounds exactly at their shared precision.
  return BigInt(lower.replace('.', '')) <= BigInt(upper.replace('.', '')) || messages.reversedRange
}

const { values, errors, defineField, setFieldValue, validate } = useForm<Draft>({
  initialValues: { setName: '', setNameTouched: false, rows: [createRow()] },
  validationSchema: {
    __type: 'VVTypedSchema',
    parse: (draft: Draft) => {
      const errors: { path: string; errors: string[] }[] = []
      if (draft.setNameTouched && !draft.setName.trim()) {
        errors.push({ path: 'setName', errors: [messages.nameRequired] })
      }

      draft.rows.forEach((row, index) => {
        const name = nameRule(draft.rows, row, index)
        const details = detailsRule(row)

        if (name !== true) errors.push({ path: `rows[${index}].name`, errors: [name] })
        if (details !== true) errors.push({ path: `rows[${index}].details`, errors: [details] })
      })

      return errors.length ? { errors } : { errors, value: draft }
    },
  },
})
const { fields, push, remove } = useFieldArray<Row>('rows')
const rowError = (index: number, field: 'name' | 'details') =>
  errors.value[`rows[${index}].${field}`]

const [setName] = defineField('setName', { validateOnModelUpdate: false })

// A name edit can change the validation result of other rows.
watch(values, () => void validate(), { deep: true })

const focusName = (key: string | number) => {
  editor.value?.querySelector<HTMLInputElement>(`[data-row-name="${key}"]`)?.focus()
}

const addRow = async () => {
  push(createRow())
  await nextTick()

  const entry = fields.value.at(-1)
  if (entry) focusName(entry.key)
}

const removeRow = async (index: number) => {
  remove(index)
  await nextTick()

  const entry = fields.value[index] ?? fields.value[index - 1]
  if (entry) focusName(entry.key)
  else editor.value?.querySelector<HTMLButtonElement>('.add')?.focus()
}
</script>

<template>
  <div ref="editor" class="editor">
    <div class="editor-body">
      <label class="field">
        {{ messages.setName }}
        <input
          v-model="setName"
          :placeholder="messages.setPlaceholder"
          :aria-invalid="Boolean(errors.setName) || undefined"
          :aria-describedby="errors.setName ? `${id}-set-error` : undefined"
          @blur="setFieldValue('setNameTouched', true, false)"
        />
      </label>
      <p v-if="errors.setName" :id="`${id}-set-error`" class="error">
        {{ errors.setName }}
      </p>

      <h2>{{ messages.attributes }}</h2>

      <fieldset
        v-for="({ key, value: row }, index) in fields"
        :key="key"
        :aria-label="messages.attribute"
      >
        <div class="row-fields">
          <label class="field">
            {{ messages.name }}
            <input
              v-model="row.name"
              :placeholder="messages.namePlaceholder"
              autocapitalize="none"
              :spellcheck="false"
              :data-row-name="key"
              :aria-invalid="Boolean(rowError(index, 'name')) || undefined"
              :aria-describedby="rowError(index, 'name') ? `${id}-name-error-${key}` : undefined"
              @blur="row.nameTouched = true"
            />
          </label>

          <label class="field">
            {{ messages.type }}
            <span class="select-control">
              <select v-model="row.type" @change="row.details = emptyDetails()">
                <option v-for="type in types" :key="type" :value="type">
                  {{ messages.types[type] }}
                </option>
              </select>
              <ChevronDown aria-hidden="true" :size="16" />
            </span>
          </label>

          <button
            class="delete"
            type="button"
            :aria-label="messages.delete.replace('{number}', String(index + 1))"
            @click="removeRow(index)"
          >
            <Trash2 aria-hidden="true" :size="17" />
          </button>
        </div>
        <p v-if="rowError(index, 'name')" :id="`${id}-name-error-${key}`" class="error">
          {{ rowError(index, 'name') }}
        </p>

        <label v-if="row.type === 'string'" class="field">
          {{ messages.choices }}
          <input
            v-model="row.details.choices"
            :placeholder="messages.choicesPlaceholder"
            :aria-invalid="Boolean(rowError(index, 'details')) || undefined"
            :aria-describedby="
              rowError(index, 'details') ? `${id}-details-error-${key}` : undefined
            "
            @blur="row.details.touched = true"
          />
        </label>

        <div v-else-if="row.type === 'id'" class="id-details">
          <label class="field">
            {{ messages.idFormat }}
            <span class="select-control">
              <select
                v-model="row.details.idFormat"
                :aria-describedby="
                  row.details.idFormat === 'sequential' ? `${id}-sequence-${key}` : undefined
                "
              >
                <option v-for="format in idFormats" :key="format" :value="format">
                  {{ messages.idFormats[format] }}
                </option>
              </select>
              <ChevronDown aria-hidden="true" :size="16" />
            </span>
          </label>
          <p v-if="row.details.idFormat === 'sequential'" :id="`${id}-sequence-${key}`">
            {{ messages.sequentialHelp }}
          </p>
        </div>

        <div v-else-if="row.type !== 'boolean'" :key="row.type" class="range">
          <label v-for="bound in ['min', 'max'] as const" :key="bound" class="field">
            {{ messages[bound] }}
            <input
              :value="row.details[bound]"
              @input="row.details[bound] = ($event.target as HTMLInputElement).value"
              :type="row.type === 'date' ? 'date' : 'text'"
              :inputmode="row.type === 'date' ? undefined : 'decimal'"
              :aria-invalid="Boolean(rowError(index, 'details')) || undefined"
              :aria-describedby="
                rowError(index, 'details') ? `${id}-details-error-${key}` : undefined
              "
              @blur="row.details.touched = true"
            />
          </label>
        </div>

        <p v-if="rowError(index, 'details')" :id="`${id}-details-error-${key}`" class="error">
          {{ rowError(index, 'details') }}
        </p>
      </fieldset>

      <button class="add" type="button" @click="addRow">
        <Plus aria-hidden="true" :size="18" />
        {{ messages.add }}
      </button>
    </div>

    <footer>
      <button class="save" type="button" disabled>{{ messages.save }}</button>
      <p>{{ messages.saveUnavailable }}</p>
    </footer>
  </div>
</template>

<style scoped>
.editor {
  display: flex;
  flex-direction: column;
  min-height: 0;
  font: var(--font-body-sm);
}

.editor-body {
  min-height: 0;
  padding: var(--space-md);
  overflow-y: auto;
  overscroll-behavior: contain;
}

h2 {
  margin: var(--space-lg) 0 var(--space-xs);
  font: var(--font-title-sm);
}

fieldset {
  min-width: 0;
  margin: 0;
  padding: var(--space-sm) 0;
  border: 0;
  border-top: 1px solid var(--color-surface-strong);
}

.field {
  display: grid;
  min-width: 0;
  gap: var(--space-xxs);
  font-weight: 500;
}

.row-fields,
.range {
  display: grid;
  align-items: end;
  gap: var(--space-xs);
}

.row-fields {
  grid-template-columns: minmax(0, 1fr) auto 44px;
}

.range {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

fieldset > .field,
.range,
.id-details {
  margin-top: var(--space-xs);
}

input,
select,
button {
  box-sizing: border-box;
  min-height: 44px;
  border: 1px solid var(--color-muted);
  border-radius: var(--radius-md);
  background: var(--color-canvas);
  color: var(--color-ink);
  font: inherit;
}

input,
select {
  width: 100%;
  min-width: 0;
  padding: var(--space-xs);
  font: var(--font-body-md);
}

.select-control {
  position: relative;
  display: block;
}

.select-control select {
  appearance: none;
  padding-inline-end: calc(var(--space-lg) + 16px);
}

.select-control svg {
  position: absolute;
  inset-block-start: 50%;
  inset-inline-end: var(--space-sm);
  transform: translateY(-50%);
  pointer-events: none;
}

.id-details p {
  margin: var(--space-xxs) 0 0;
  color: var(--color-muted);
}

input::placeholder {
  color: var(--color-muted);
  opacity: 1;
}

input:focus-visible,
select:focus-visible,
button:focus-visible {
  outline: 2px solid var(--color-ink);
  outline-offset: 1px;
}

button {
  cursor: pointer;
  font: var(--font-button);
}

button:hover:not(:disabled) {
  background: var(--color-surface-strong);
}

.delete {
  display: grid;
  width: 44px;
  place-items: center;
  border-color: transparent;
}

.add {
  display: inline-flex;
  align-items: center;
  gap: var(--space-xs);
  padding: var(--space-xs) var(--space-sm);
}

.error {
  margin: var(--space-xxs) 0 0;
  color: color-mix(in srgb, var(--color-error) 68%, var(--color-ink));
}

footer {
  display: grid;
  flex: none;
  gap: var(--space-xs);
  padding: var(--space-sm) var(--space-md);
  border-top: 1px solid var(--color-hairline);
  background: var(--color-surface-soft);
}

.save {
  border-color: transparent;
  background: var(--color-primary-disabled);
  color: var(--color-muted);
  cursor: default;
}

footer p {
  margin: 0;
  color: var(--color-muted);
  font: var(--font-caption);
  text-align: center;
}

@media (max-width: 360px) {
  .row-fields {
    grid-template-columns: minmax(0, 1fr) 44px;
  }

  .row-fields label:first-child {
    grid-column: 1 / -1;
  }

  .range {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>
