<script setup lang="ts">
import { computed, ref, useId } from 'vue'
import { useI18n } from 'vue-i18n'

import FormField from '@/components/FormField.vue'
import type { District, Prefecture } from '@/services'
import { isLatinQuery } from '@/utils/areaSearch'

const { t } = useI18n({ useScope: 'global' })

type Area = District | Prefecture

const props = defineProps<{
  mode: 'district' | 'prefecture'
  results: Area[]
  loading: boolean
  unavailable: boolean
  disabled?: boolean
  selectionRequired?: boolean
}>()
const emit = defineEmits<{
  select: [area: Area]
  clearSelection: []
  search: [text: string]
  clearSearch: []
}>()
const message = (key: string) => t(`components.AreaSearch.${props.mode}.${key}`)
const text = ref('')
const focused = ref(false)
const composing = ref(false)
const active = ref(-1)
const open = ref(false)
const listId = useId()
const expanded = computed(
  () => !props.disabled && focused.value && open.value && props.results.length > 0,
)
const optionId = (index: number) => `${listId}-${index}`
const showEnglish = computed(() => isLatinQuery(text.value))
const displayLabel = (area: Area) => (showEnglish.value ? (area.labelEn ?? area.label) : area.label)

const update = (event: Event) => {
  const value = (event.target as HTMLInputElement).value
  if (text.value !== value) emit('clearSelection')

  text.value = value
  if (composing.value) return

  active.value = -1
  open.value = props.mode === 'prefecture' || Boolean(text.value.trim())
  emit('search', text.value)
}

const startComposition = () => {
  composing.value = true
  open.value = false
  emit('clearSearch')
}

const finishComposition = (event: CompositionEvent) => {
  composing.value = false
  update(event)
}

const choose = (area: Area) => {
  text.value = displayLabel(area)
  open.value = false
  active.value = -1
  emit('clearSearch')
  emit('select', area)
}

const handleKey = (event: KeyboardEvent) => {
  if (composing.value || event.isComposing) return

  if (event.key === 'Escape' && open.value) {
    event.preventDefault()
    open.value = false
    active.value = -1
  } else if (expanded.value && (event.key === 'ArrowDown' || event.key === 'ArrowUp')) {
    event.preventDefault()
    const last = props.results.length - 1
    active.value =
      event.key === 'ArrowDown'
        ? active.value >= last
          ? 0
          : active.value + 1
        : active.value <= 0
          ? last
          : active.value - 1
    document.getElementById(optionId(active.value))?.scrollIntoView?.({ block: 'nearest' })
  } else if (expanded.value && event.key === 'Enter') {
    const area = props.results[active.value]
    if (area || props.mode === 'prefecture') event.preventDefault()
    if (area) choose(area)
  }
}

const focus = () => {
  focused.value = true
  if (props.mode === 'prefecture' && !text.value) open.value = true
}

const blur = () => {
  focused.value = false
  active.value = -1
}
</script>

<template>
  <div class="area-search">
    <FormField :label="message('label')">
      <input
        class="text-input"
        :value="text"
        :placeholder="message('placeholder')"
        :disabled="disabled"
        role="combobox"
        autocomplete="off"
        aria-autocomplete="list"
        :aria-expanded="expanded"
        :aria-controls="listId"
        :aria-invalid="selectionRequired || undefined"
        :aria-describedby="selectionRequired ? `${listId}-error` : undefined"
        :aria-activedescendant="expanded && active >= 0 ? optionId(active) : undefined"
        @focus="focus"
        @blur="blur"
        @input="update"
        @compositionstart="startComposition"
        @compositionend="finishComposition"
        @keydown="handleKey"
      />
    </FormField>
    <p v-if="selectionRequired" :id="`${listId}-error`" class="error" role="alert">
      {{ message('selectionRequired') }}
    </p>
    <ul
      v-show="expanded"
      :id="listId"
      class="area-results"
      role="listbox"
      :aria-label="message('label')"
    >
      <li
        v-for="(area, index) in results"
        :id="optionId(index)"
        :key="area.code"
        role="option"
        :aria-selected="index === active"
        @pointerdown.prevent
        @click="choose(area)"
      >
        {{ displayLabel(area) }}
      </li>
    </ul>
    <div v-if="!disabled && focused && open && !expanded" class="area-status" role="status">
      {{ unavailable ? message('unavailable') : loading ? message('loading') : message('empty') }}
    </div>
  </div>
</template>

<style scoped>
.area-search {
  display: grid;
  gap: var(--space-xs);
}

.error {
  margin: 0;
  color: color-mix(in srgb, var(--color-error) 68%, var(--color-ink));
}

.area-results,
.area-status {
  margin: 0;
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-md);
  background: var(--color-canvas);
  font: var(--font-body-sm);
  letter-spacing: var(--letter-spacing-body-sm);
  overflow-wrap: anywhere;
}

.area-results {
  max-height: clamp(44px, calc(100dvh - 160px), 264px);
  overflow-y: auto;
  overscroll-behavior: contain;
  padding: var(--space-xxs);
  list-style: none;
}

.area-results li {
  box-sizing: border-box;
  display: flex;
  align-items: center;
  min-height: 44px;
  padding: var(--space-xs) var(--space-sm);
  border-radius: var(--radius-xs);
  cursor: pointer;
}

.area-results li:hover,
.area-results li[aria-selected='true'] {
  background: var(--color-surface-strong);
}

.area-status {
  padding: var(--space-xs) var(--space-sm);
  color: var(--color-body);
}
</style>
