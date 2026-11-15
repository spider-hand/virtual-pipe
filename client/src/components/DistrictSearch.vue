<script setup lang="ts">
import { computed, ref, useId } from 'vue'
import { useI18n } from 'vue-i18n'

import { useDistrictsQuery } from '@/composables/useDistrictsQuery'
import type { District } from '@/services'

const { t } = useI18n({ useScope: 'global' })

const props = defineProps<{ disabled?: boolean }>()
const emit = defineEmits<{ select: [district: District]; clearSelection: [] }>()
const { results, loading, unavailable, search, clear } = useDistrictsQuery()
const text = ref('')
const focused = ref(false)
const composing = ref(false)
const active = ref(-1)
const open = ref(false)
const inputId = useId()
const listId = useId()
const expanded = computed(
  () => !props.disabled && focused.value && open.value && results.value.length > 0,
)
const optionId = (index: number) => `${listId}-${index}`

const update = (event: Event) => {
  const value = (event.target as HTMLInputElement).value
  if (text.value !== value) emit('clearSelection')

  text.value = value
  if (composing.value) return

  active.value = -1
  open.value = Boolean(text.value.trim())
  search(text.value)
}

const startComposition = () => {
  composing.value = true
  open.value = false
  clear()
}

const finishComposition = (event: CompositionEvent) => {
  composing.value = false
  update(event)
}

const choose = (district: District) => {
  text.value = district.label
  open.value = false
  active.value = -1
  clear()
  emit('select', district)
}

const handleKey = (event: KeyboardEvent) => {
  if (composing.value || event.isComposing) return

  if (event.key === 'Escape' && open.value) {
    event.preventDefault()
    open.value = false
    active.value = -1
  } else if (expanded.value && (event.key === 'ArrowDown' || event.key === 'ArrowUp')) {
    event.preventDefault()
    const last = results.value.length - 1
    active.value =
      event.key === 'ArrowDown'
        ? active.value >= last
          ? 0
          : active.value + 1
        : active.value <= 0
          ? last
          : active.value - 1
    document.getElementById(optionId(active.value))?.scrollIntoView?.({ block: 'nearest' })
  } else if (expanded.value && event.key === 'Enter' && results.value[active.value]) {
    event.preventDefault()
    choose(results.value[active.value])
  }
}

const blur = () => {
  focused.value = false
  active.value = -1
}
</script>

<template>
  <div class="district-search">
    <label :for="inputId">{{ t('components.DistrictSearch.label') }}</label>
    <input
      :id="inputId"
      :value="text"
      :placeholder="t('components.DistrictSearch.placeholder')"
      :disabled="disabled"
      role="combobox"
      autocomplete="off"
      aria-autocomplete="list"
      :aria-expanded="expanded"
      :aria-controls="listId"
      :aria-activedescendant="expanded && active >= 0 ? optionId(active) : undefined"
      @focus="focused = true"
      @blur="blur"
      @input="update"
      @compositionstart="startComposition"
      @compositionend="finishComposition"
      @keydown="handleKey"
    />
    <ul
      v-show="expanded"
      :id="listId"
      class="district-results"
      role="listbox"
      :aria-label="t('components.DistrictSearch.label')"
    >
      <li
        v-for="(district, index) in results"
        :id="optionId(index)"
        :key="district.code"
        role="option"
        :aria-selected="index === active"
        @pointerdown.prevent
        @click="choose(district)"
      >
        {{ district.label }}
      </li>
    </ul>
    <div v-if="!disabled && focused && open && !expanded" class="district-status" role="status">
      {{
        unavailable
          ? t('components.DistrictSearch.unavailable')
          : loading
            ? t('components.DistrictSearch.loading')
            : t('components.DistrictSearch.empty')
      }}
    </div>
  </div>
</template>

<style scoped>
.district-search {
  box-sizing: border-box;
  display: grid;
  gap: var(--space-xs);
  padding: var(--space-sm);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-lg);
  background: var(--color-surface-soft);
  color: var(--color-ink);
}

label {
  font: var(--font-title-sm);
  letter-spacing: var(--letter-spacing-title-sm);
}

input {
  box-sizing: border-box;
  width: 100%;
  min-height: 44px;
  padding: var(--space-xs) var(--space-md);
  border: 1px solid var(--color-muted);
  border-radius: var(--radius-md);
  background: var(--color-canvas);
  color: inherit;
  font: var(--font-body-md);
  letter-spacing: var(--letter-spacing-body-md);
}

input::placeholder {
  color: var(--color-muted);
  opacity: 1;
}

input:focus {
  outline: 2px solid var(--color-ink);
  outline-offset: 1px;
}

.district-results,
.district-status {
  margin: 0;
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-md);
  background: var(--color-canvas);
  font: var(--font-body-sm);
  letter-spacing: var(--letter-spacing-body-sm);
  overflow-wrap: anywhere;
}

.district-results {
  max-height: clamp(44px, calc(100dvh - 160px), 264px);
  overflow-y: auto;
  overscroll-behavior: contain;
  padding: var(--space-xxs);
  list-style: none;
}

.district-results li {
  box-sizing: border-box;
  display: flex;
  align-items: center;
  min-height: 44px;
  padding: var(--space-xs) var(--space-sm);
  border-radius: var(--radius-xs);
  cursor: pointer;
}

.district-results li:hover,
.district-results li[aria-selected='true'] {
  background: var(--color-surface-strong);
}

.district-status {
  padding: var(--space-xs) var(--space-sm);
  color: var(--color-body);
}
</style>
