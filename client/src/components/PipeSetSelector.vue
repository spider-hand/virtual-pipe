<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import FormField from '@/components/FormField.vue'
import SelectField from '@/components/SelectField.vue'
import type { PipeSetSummary } from '@/services'

const props = defineProps<{ sets: PipeSetSummary[]; loading: boolean; failed: boolean }>()

const selectedId = defineModel<string>({ required: true })

const { t } = useI18n({ useScope: 'global' })

const options = computed(() =>
  props.sets.length
    ? props.sets.map(({ id, name }) => ({ value: id, label: name }))
    : [
        {
          value: '',
          label: t(`components.PipeSetSelector.${props.loading ? 'loading' : 'empty'}`),
        },
      ],
)
</script>

<template>
  <div class="pipeset-selector" :aria-busy="loading">
    <FormField v-if="!failed || sets.length" :label="t('components.PipeSetSelector.label')">
      <SelectField v-model="selectedId" :options="options" :disabled="!sets.length" />
    </FormField>
    <p v-if="failed" role="alert">{{ t('components.PipeSetSelector.loadFailed') }}</p>
  </div>
</template>

<style scoped>
.pipeset-selector {
  display: grid;
  box-sizing: border-box;
  gap: var(--space-xxs);
  padding: var(--space-xs);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-lg);
  background: var(--color-canvas);
  color: var(--color-ink);
  font: var(--font-body-sm);
}

p {
  margin: 0;
}
</style>
