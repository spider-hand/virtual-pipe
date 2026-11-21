<script setup lang="ts">
import { computed, ref, shallowRef, toRef, useId, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import AreaSearch from '@/components/AreaSearch.vue'
import AttributePreview from '@/components/AttributePreview.vue'
import DistrictSearch from '@/components/DistrictSearch.vue'
import FormField from '@/components/FormField.vue'
import SelectField from '@/components/SelectField.vue'
import { useAttributeSetsQuery } from '@/composables/useAttributeSetsQuery'
import { usePipeSetsQuery } from '@/composables/usePipeSetsQuery'
import { usePrefecturesQuery } from '@/composables/usePrefecturesQuery'
import type { District, Prefecture } from '@/services'
import { isLatinQuery, normalizeLatinQuery } from '@/utils/areaSearch'
import { getSetNameError } from '@/utils/validation'

const { t } = useI18n({ useScope: 'global' })

const props = defineProps<{ active: boolean }>()

const emit = defineEmits<{
  areaChange: [area: District | Prefecture | null]
  pipesetReady: [id: string]
}>()

const id = useId()

const { attributeSets, isAttributeSetsFetching, isAttributeSetsError } = useAttributeSetsQuery(
  toRef(() => props.active),
)

const { pipeSetStatus, isPipeSetBusy, createPipeSet } = usePipeSetsQuery({
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
  ...attributeSets.value.map(({ id, name }) => ({ value: id, label: name })),
])

const areaTypes = ['district', 'prefecture'] as const
const areaType = ref<(typeof areaTypes)[number]>('district')
const area = shallowRef<District | Prefecture | null>(null)

const prefectureSearch = ref('')

const { prefectures, isPrefecturesFetching, isPrefecturesError } = usePrefecturesQuery(
  toRef(() => props.active),
)

const normalizeQuery = (query: string) => query.normalize('NFKC').replace(/\s+/gu, '')

const prefectureResults = computed(() => {
  const text = prefectureSearch.value
  if (isLatinQuery(text)) {
    const query = normalizeLatinQuery(text)

    return prefectures.value.filter(({ labelEn }) =>
      normalizeLatinQuery(labelEn ?? '').includes(query),
    )
  }

  const query = normalizeQuery(text)
  return prefectures.value.filter(({ label }) => normalizeQuery(label).includes(query))
})

const selectedSet = computed(() => attributeSets.value.find((set) => set.id === selectedId.value))

const saveDisabled = computed(
  () =>
    isPipeSetBusy.value ||
    isAttributeSetsFetching.value ||
    isAttributeSetsError.value ||
    !attributeSets.value.length,
)
const setInvalid = computed(
  () => submitAttempted.value && !saveDisabled.value && !selectedSet.value,
)

watch(attributeSets, () => {
  if (!selectedSet.value) selectedId.value = ''
})

const setArea = (next: District | Prefecture | null) => {
  if (area.value === next) return

  area.value = next
  emit('areaChange', next)
}

watch(areaType, () => {
  setArea(null)
  prefectureSearch.value = ''
})

const save = () => {
  if (saveDisabled.value) return

  submitAttempted.value = true
  nameTouched.value = true
  if (nameError.value || !selectedSet.value || !area.value) return

  submitAttempted.value = false
  void createPipeSet({
    name: name.value.trim(),
    attributeSetId: selectedSet.value.id,
    ...(areaType.value === 'district'
      ? { districtId: area.value.code }
      : { prefectureId: area.value.code }),
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
          :disabled="isPipeSetBusy"
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
      <p v-if="isAttributeSetsFetching" role="status">
        {{ t('components.PipeSetGenerator.loading') }}
      </p>
      <p v-else-if="isAttributeSetsError" role="alert">
        {{ t('components.PipeSetGenerator.loadFailed') }}
      </p>
      <p v-else-if="attributeSets.length === 0" role="status">
        {{ t('components.PipeSetGenerator.empty') }}
      </p>
      <p v-else-if="setInvalid" :id="`${id}-set-error`" class="error" role="alert">
        {{ t('components.PipeSetGenerator.setRequired') }}
      </p>
    </div>

    <AttributePreview v-if="selectedSet" :attributes="selectedSet.attributes" />

    <fieldset class="area-types" :disabled="isPipeSetBusy">
      <legend>{{ t('components.PipeSetGenerator.areaType') }}</legend>
      <label v-for="type in areaTypes" :key="type">
        <input v-model="areaType" type="radio" :name="`${id}-area-type`" :value="type" />
        {{ t(`components.PipeSetGenerator.${type}`) }}
      </label>
    </fieldset>

    <DistrictSearch
      v-if="areaType === 'district'"
      :disabled="isPipeSetBusy"
      :selection-required="submitAttempted && !area"
      @select="setArea"
      @clear-selection="setArea(null)"
    />
    <AreaSearch
      v-else
      mode="prefecture"
      :results="prefectureResults"
      :loading="isPrefecturesFetching"
      :unavailable="isPrefecturesError"
      :disabled="isPipeSetBusy"
      :selection-required="submitAttempted && !area"
      @search="prefectureSearch = $event"
      @clear-search="prefectureSearch = ''"
      @select="setArea"
      @clear-selection="setArea(null)"
    />

    <button class="save" type="submit" :disabled="saveDisabled">
      {{ t('components.PipeSetGenerator.save') }}
    </button>
    <p v-if="pipeSetStatus !== 'idle'" role="status">
      {{ t(`components.PipeSetGenerator.${pipeSetStatus}`) }}
    </p>
  </form>
</template>

<style scoped>
.generator {
  display: grid;
  gap: var(--space-md);
  padding: var(--space-md);
  font: var(--font-body-sm);
}

.area-types {
  display: flex;
  flex-wrap: wrap;
  gap: 0 var(--space-md);
  margin: 0;
  padding: 0;
  border: 0;
}

.area-types legend {
  padding: 0;
}

.area-types label {
  display: inline-flex;
  align-items: center;
  gap: var(--space-xs);
  min-height: 44px;
  cursor: pointer;
}

.area-types input {
  margin: 0;
  accent-color: var(--color-primary);
}

.set-picker {
  display: grid;
  gap: var(--space-xs);
}

.error {
  color: color-mix(in srgb, var(--color-error) 68%, var(--color-ink));
}

p {
  margin: 0;
  color: var(--color-body);
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
