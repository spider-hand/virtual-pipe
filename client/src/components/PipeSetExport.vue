<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'

import AttributePreview from '@/components/AttributePreview.vue'
import FormField from '@/components/FormField.vue'
import SelectField from '@/components/SelectField.vue'
import { usePipeSetDownload } from '@/composables/usePipeSetDownload'
import type { PipeSetSummary } from '@/services'

defineProps<{ selectedSet?: PipeSetSummary }>()

const { t } = useI18n({ useScope: 'global' })

const formats = [
  { value: 'csv', label: 'CSV' },
  { value: 'parquet', label: 'Parquet' },
] as const

const { downloadPipeSet, isPipeSetDownloadPending, isPipeSetDownloadError } = usePipeSetDownload()

const format = ref<(typeof formats)[number]['value']>('csv')
</script>

<template>
  <div class="export-panel">
    <template v-if="selectedSet">
      <p class="set-name">{{ selectedSet.name }}</p>
      <AttributePreview
        v-if="selectedSet.attributeDefinitions?.length"
        :attributes="selectedSet.attributeDefinitions"
      />
      <p v-else>{{ t('components.PipeSetExport.noDefinitions') }}</p>
    </template>
    <p v-else>{{ t('components.PipeSetExport.noSelection') }}</p>

    <FormField :label="t('components.PipeSetExport.format')">
      <SelectField v-model="format" :options="formats" :disabled="!selectedSet" />
    </FormField>

    <div class="download">
      <button
        type="button"
        :disabled="!selectedSet || isPipeSetDownloadPending"
        @click="selectedSet && downloadPipeSet(selectedSet.id, format)"
      >
        {{ t('components.PipeSetExport.action') }}
      </button>
      <p v-if="isPipeSetDownloadPending" role="status">
        {{ t('components.PipeSetExport.preparing') }}
      </p>
      <p v-if="isPipeSetDownloadError" role="alert">{{ t('components.PipeSetExport.failed') }}</p>
    </div>
  </div>
</template>

<style scoped>
.export-panel {
  display: grid;
  gap: var(--space-md);
  padding: var(--space-md);
  font: var(--font-body-sm);
}

p {
  margin: 0;
  color: var(--color-body);
  overflow-wrap: anywhere;
}

.set-name {
  color: var(--color-ink);
  font: var(--font-title-sm);
}

.download {
  display: grid;
  gap: var(--space-xs);
}

button {
  min-height: 44px;
  padding: var(--space-xs) var(--space-md);
  border: 1px solid transparent;
  border-radius: var(--radius-md);
  background: var(--color-primary);
  color: var(--color-on-primary);
  cursor: pointer;
  font: var(--font-button);
}

button:hover:not(:disabled) {
  background: var(--color-primary-active);
}

button:focus-visible {
  outline: 2px solid var(--color-ink);
  outline-offset: 2px;
}

button:disabled {
  background: var(--color-primary-disabled);
  color: var(--color-muted);
  cursor: default;
}
</style>
