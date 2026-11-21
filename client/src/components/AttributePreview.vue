<script setup lang="ts">
import { useId } from 'vue'
import { useI18n } from 'vue-i18n'

import type { AttributeDefinition } from '@/services'

defineProps<{ attributes: AttributeDefinition[] }>()

const { t } = useI18n({ useScope: 'global' })

const id = useId()

const details = (attribute: AttributeDefinition) => {
  switch (attribute.type) {
    case 'string':
      return attribute.choices.join(t('components.AttributePreview.choiceSeparator'))
    case 'integer':
    case 'decimal':
    case 'date':
      return t('components.AttributePreview.range', { min: attribute.min, max: attribute.max })
    case 'id':
      return t(`components.AttributePreview.idFormats.${attribute.idFormat}`)
    case 'boolean':
      return undefined
  }
}
</script>

<template>
  <section :aria-labelledby="`${id}-preview`">
    <h2 :id="`${id}-preview`">{{ t('components.AttributePreview.preview') }}</h2>
    <dl class="preview">
      <div v-for="attribute in attributes" :key="attribute.name">
        <dt>{{ attribute.name }}</dt>
        <dd>{{ t(`components.AttributePreview.types.${attribute.type}`) }}</dd>
        <dd v-if="attribute.type !== 'boolean'">{{ details(attribute) }}</dd>
      </div>
    </dl>
  </section>
</template>

<style scoped>
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

dd {
  margin: 0;
  color: var(--color-body);
}

dd + dd {
  grid-column: 1 / -1;
}
</style>
