<script setup lang="ts">
import { computed, ref, shallowRef, toRef, useId, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import DistrictSearch from '@/components/DistrictSearch.vue'
import FormField from '@/components/FormField.vue'
import SelectField from '@/components/SelectField.vue'
import { useAttributeSetsQuery } from '@/composables/useAttributeSetsQuery'
import { usePipeSetsQuery } from '@/composables/usePipeSetsQuery'
import type { AttributeDefinition, District } from '@/services'
import { getSetNameError } from '@/utils/validation'

const { t } = useI18n({ useScope: 'global' })
const props = defineProps<{ active: boolean }>()
const emit = defineEmits<{
  districtChange: [district: District | null]
  pipesetReady: [id: string]
}>()
const id = useId()
const { sets, loading, failed } = useAttributeSetsQuery(toRef(() => props.active))
const { status, busy, submit } = usePipeSetsQuery({
  onSucceeded: (id) => emit('pipesetReady', id),
})
const selectedId = ref('')
const name = ref('')
const nameTouched = ref(false)
const submitAttempted = ref(false)
const nameError = computed(() => {
  const error = getSetNameError(name.value, nameTouched.value)
  if (error === 'required') return t('components.PipeSetGenerator.nameRequired')
  if (error === 'tooLong') return t('components.PipeSetGenerator.nameTooLong')
  return undefined
})
const options = computed(() => [
  { value: '', label: t('components.PipeSetGenerator.selectSet'), disabled: true },
  ...sets.value.map(({ id, name }) => ({ value: id, label: name })),
])
const district = shallowRef<District | null>(null)
const selectedSet = computed(() => sets.value.find((set) => set.id === selectedId.value))
const saveDisabled = computed(
  () => busy.value || loading.value || failed.value || !sets.value.length,
)
const setInvalid = computed(
  () => submitAttempted.value && !saveDisabled.value && !selectedSet.value,
)

watch(sets, () => {
  if (!selectedSet.value) selectedId.value = ''
})

const details = (attribute: AttributeDefinition) => {
  switch (attribute.type) {
    case 'string':
      return attribute.choices.join(t('components.PipeSetGenerator.choiceSeparator'))
    case 'integer':
    case 'decimal':
    case 'date':
      return t('components.PipeSetGenerator.range', { min: attribute.min, max: attribute.max })
    case 'id':
      return t(`components.PipeSetGenerator.idFormats.${attribute.idFormat}`)
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
  if (saveDisabled.value) return

  submitAttempted.value = true
  nameTouched.value = true
  if (nameError.value || !selectedSet.value || !district.value) return

  submitAttempted.value = false
  void submit({
    name: name.value.trim(),
    attributeSetId: selectedSet.value.id,
    districtId: district.value.code,
  })
}
</script>

<template>
  <form class="generator" novalidate @submit.prevent="save">
    <div class="set-picker">
      <FormField :label="t('components.PipeSetGenerator.name')">
        <input
          class="text-input"
          v-model="name"
          :disabled="busy"
          :aria-invalid="Boolean(nameError) || undefined"
          :aria-describedby="nameError ? `${id}-name-error` : undefined"
          required
          @blur="nameTouched = true"
        />
      </FormField>
      <p v-if="nameError" :id="`${id}-name-error`" class="error" role="alert">
        {{ nameError }}
      </p>
    </div>

    <div class="set-picker">
      <FormField :label="t('components.PipeSetGenerator.attributeSet')">
        <SelectField
          v-model="selectedId"
          :options="options"
          :disabled="saveDisabled"
          :aria-invalid="setInvalid || undefined"
          :aria-describedby="setInvalid ? `${id}-set-error` : undefined"
          required
        />
      </FormField>
      <p v-if="loading" role="status">{{ t('components.PipeSetGenerator.loading') }}</p>
      <p v-else-if="failed" role="alert">{{ t('components.PipeSetGenerator.loadFailed') }}</p>
      <p v-else-if="sets.length === 0" role="status">
        {{ t('components.PipeSetGenerator.empty') }}
      </p>
      <p v-else-if="setInvalid" :id="`${id}-set-error`" class="error" role="alert">
        {{ t('components.PipeSetGenerator.setRequired') }}
      </p>
    </div>

    <section v-if="selectedSet" :aria-labelledby="`${id}-preview`">
      <h2 :id="`${id}-preview`">{{ t('components.PipeSetGenerator.preview') }}</h2>
      <dl class="preview">
        <div v-for="attribute in selectedSet.attributes" :key="attribute.name">
          <dt>{{ attribute.name }}</dt>
          <dd>{{ t(`components.PipeSetGenerator.types.${attribute.type}`) }}</dd>
          <dd v-if="attribute.type !== 'boolean'">{{ details(attribute) }}</dd>
        </div>
      </dl>
    </section>

    <DistrictSearch
      :disabled="busy"
      :selection-required="submitAttempted && !district"
      @select="setDistrict"
      @clear-selection="setDistrict(null)"
    />

    <button class="save" type="submit" :disabled="saveDisabled">
      {{ t('components.PipeSetGenerator.save') }}
    </button>
    <p v-if="status !== 'idle'" role="status">{{ t(`components.PipeSetGenerator.${status}`) }}</p>
  </form>
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

h2 {
  margin: 0;
  font: var(--font-title-sm);
}

.error {
  color: color-mix(in srgb, var(--color-error) 68%, var(--color-ink));
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
