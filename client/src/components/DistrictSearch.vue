<script setup lang="ts">
import { computed, ref, useId } from 'vue'

import { useDistrictsQuery } from '@/composables/useDistrictsQuery'
import en from '@/locales/en.json'
import ja from '@/locales/ja.json'
import type { District } from '@/services'

const locale = navigator.language.toLowerCase().startsWith('ja') ? ja : en
const messages = locale.components.DistrictSearch

const emit = defineEmits<{ select: [district: District] }>()
const { results, loading, unavailable, search, clear } = useDistrictsQuery()
const text = ref('')
const focused = ref(false)
const composing = ref(false)
const active = ref(-1)
const open = ref(false)
const inputId = useId()
const listId = useId()
const expanded = computed(() => focused.value && open.value && results.value.length > 0)
const optionId = (index: number) => `${listId}-${index}`

const update = (event: Event) => {
  text.value = (event.target as HTMLInputElement).value
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
  <div>
    <label :for="inputId">{{ messages.label }}</label>
    <input
      :id="inputId"
      :value="text"
      :placeholder="messages.placeholder"
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
    <ul v-show="expanded" :id="listId" role="listbox" :aria-label="messages.label">
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
    <div v-if="focused && open && !expanded" role="status">
      {{ unavailable ? messages.unavailable : loading ? messages.loading : messages.empty }}
    </div>
  </div>
</template>
