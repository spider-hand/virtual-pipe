<script setup lang="ts">
import { computed, ref, shallowRef, useId, watch } from 'vue'

import DistrictSearch from '@/components/DistrictSearch.vue'
import SelectField from '@/components/SelectField.vue'
import { useAttributeSetsQuery } from '@/composables/useAttributeSetsQuery'
import { usePipeSetGenerationQuery } from '@/composables/usePipeSetGenerationQuery'
import en from '@/locales/en.json'
import ja from '@/locales/ja.json'
import type { AttributeDefinition, District } from '@/services'

const locale = navigator.language.toLowerCase().startsWith('ja') ? ja : en
const messages = locale.components.PipeSetGenerator
const props = defineProps<{ active: boolean }>()
const emit = defineEmits<{
  districtChange: [district: District | null]
  pipesetReady: [id: string]
}>()
const id = useId()
const { sets, loading, failed, load } = useAttributeSetsQuery()
const { status, busy, submit } = usePipeSetGenerationQuery({
  onSucceeded: (id) => emit('pipesetReady', id),
})
const selectedId = ref('')
const options = computed(() => [
  { value: '', label: messages.selectSet, disabled: true },
  ...sets.value.map(({ id, name }) => ({ value: id, label: name })),
])
const district = shallowRef<District | null>(null)
const selectedSet = computed(() => sets.value.find((set) => set.id === selectedId.value))

watch(
  () => props.active,
  (active) => {
    if (active) void load()
  },
  { immediate: true },
)

watch(sets, () => {
  if (!selectedSet.value) selectedId.value = ''
})

const details = (attribute: AttributeDefinition) => {
  switch (attribute.type) {
    case 'string':
      return attribute.choices.join(messages.choiceSeparator)
    case 'integer':
    case 'decimal':
    case 'date':
      return messages.range.replace('{min}', attribute.min).replace('{max}', attribute.max)
    case 'id':
      return messages.idFormats[attribute.idFormat]
    case 'boolean':
      return undefined
  }
}

const setDistrict = (next: District | null) => {
  if (district.value === next) return

  district.value = next
  emit('districtChange', next)
}

const save = () => {
  if (!selectedSet.value || !district.value) return

  void submit({ attributeSetId: selectedSet.value.id, districtId: district.value.code })
}
</script>

<template>
  <div class="generator">
    <div class="set-picker">
      <label :for="`${id}-set`">{{ messages.attributeSet }}</label>
      <SelectField
        :id="`${id}-set`"
        v-model="selectedId"
        :options="options"
        :disabled="busy || loading || failed || sets.length === 0"
      />
      <p v-if="loading" role="status">{{ messages.loading }}</p>
      <p v-else-if="failed" role="alert">{{ messages.loadFailed }}</p>
      <p v-else-if="sets.length === 0" role="status">{{ messages.empty }}</p>
    </div>

    <section v-if="selectedSet" :aria-labelledby="`${id}-preview`">
      <h2 :id="`${id}-preview`">{{ messages.preview }}</h2>
      <dl class="preview">
        <div v-for="attribute in selectedSet.attributes" :key="attribute.name">
          <dt>{{ attribute.name }}</dt>
          <dd>{{ messages.types[attribute.type] }}</dd>
          <dd v-if="attribute.type !== 'boolean'">{{ details(attribute) }}</dd>
        </div>
      </dl>
    </section>

    <DistrictSearch :disabled="busy" @select="setDistrict" @clear-selection="setDistrict(null)" />

    <button
      class="save"
      type="button"
      :disabled="busy || !selectedSet || !district || loading || failed"
      @click="save"
    >
      {{ messages.save }}
    </button>
    <p v-if="status !== 'idle'" role="status">{{ messages[status] }}</p>
  </div>
</template>

<style scoped>
.generator {
  display: grid;
  gap: var(--space-md);
  padding: var(--space-md);
  font: var(--font-body-sm);
}

.set-picker {
  display: grid;
  gap: var(--space-xs);
}

label,
h2 {
  margin: 0;
  font: var(--font-title-sm);
}

.preview {
  display: grid;
  margin: var(--space-xs) 0 0;
  padding: 0 var(--space-sm);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-md);
  background: var(--color-surface-soft);
  overflow-wrap: anywhere;
}

.preview > div {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: var(--space-xxs) var(--space-sm);
  padding: var(--space-xs) 0;
}

.preview > div + div {
  border-top: 1px solid var(--color-hairline);
}

dt {
  font-weight: 600;
}

dd,
p {
  margin: 0;
  color: var(--color-body);
}

dd + dd {
  grid-column: 1 / -1;
}

button {
  min-height: 44px;
  padding: var(--space-xs) var(--space-md);
  border: 1px solid transparent;
  border-radius: var(--radius-md);
  cursor: pointer;
  font: var(--font-button);
}

.save {
  background: var(--color-primary);
  color: var(--color-on-primary);
}

.save:hover:not(:disabled) {
  background: var(--color-primary-active);
}

.save:disabled {
  background: var(--color-primary-disabled);
  color: var(--color-body);
  cursor: default;
}

button:focus-visible {
  outline: 2px solid var(--color-ink);
  outline-offset: 2px;
}
</style>
