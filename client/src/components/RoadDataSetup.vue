<script setup lang="ts">
import { ArrowLeft } from '@lucide/vue'
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { RouterLink } from 'vue-router'

import FormField from '@/components/FormField.vue'
import SelectField from '@/components/SelectField.vue'

const { t } = useI18n()
const regions = [
  'japan',
  'chubu',
  'chugoku',
  'hokkaido',
  'kansai',
  'kanto',
  'kyushu',
  'shikoku',
  'tohoku',
] as const
const region = ref<(typeof regions)[number] | ''>('')
const options = computed(() => [
  { value: '' as const, label: t('components.RoadDataSetup.selectRegion'), disabled: true },
  ...regions.map((value) => ({ value, label: t(`components.RoadDataSetup.regions.${value}`) })),
])
</script>

<template>
  <main class="road-data-setup">
    <div class="content">
      <RouterLink class="back-link" :to="{ name: 'map' }">
        <ArrowLeft :size="16" aria-hidden="true" />
        {{ t('components.RoadDataSetup.back') }}
      </RouterLink>

      <h1>{{ t('components.RoadDataSetup.title') }}</h1>

      <section class="coverage" aria-labelledby="road-data-coverage-heading">
        <h2 id="road-data-coverage-heading">{{ t('components.RoadDataSetup.coverage') }}</h2>
        <p>{{ t('components.RoadDataSetup.activeRegion') }}</p>
      </section>

      <div class="prepare">
        <FormField class="region-field" :label="t('components.RoadDataSetup.region')">
          <SelectField v-model="region" :options="options" />
        </FormField>
        <button type="button" disabled>
          {{ t('components.RoadDataSetup.download') }}
        </button>
      </div>
    </div>
  </main>
</template>

<style scoped>
.road-data-setup {
  box-sizing: border-box;
  min-height: 100dvh;
  padding: clamp(var(--space-md), 5vw, var(--space-xxl));
  background: var(--color-canvas);
  color: var(--color-ink);
  font: var(--font-body-md);
}

.content {
  max-width: 480px;
  margin-inline: auto;
}

.back-link {
  display: inline-flex;
  min-height: 44px;
  align-items: center;
  gap: var(--space-xs);
  color: inherit;
  font: var(--font-nav-link);
  text-underline-offset: 3px;
}

h1 {
  margin: var(--space-md) 0 var(--space-lg);
  font: var(--font-display-md);
  letter-spacing: var(--letter-spacing-display-md);
}

@media (max-width: 480px) {
  h1 {
    font: var(--font-display-sm);
    letter-spacing: var(--letter-spacing-display-sm);
  }
}

h2 {
  margin: 0 0 var(--space-xs);
  font: var(--font-title-sm);
}

.coverage {
  padding: var(--space-md);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-lg);
  background: var(--color-surface-soft);
}

.prepare {
  display: grid;
  justify-items: start;
  gap: var(--space-sm);
  margin-block-start: var(--space-lg);
}

.region-field {
  width: 100%;
}

p {
  margin: 0;
}

button {
  min-height: 44px;
  padding: var(--space-sm) var(--space-md);
  border: 0;
  border-radius: var(--radius-md);
  background: var(--color-primary-disabled);
  color: var(--color-body);
  font: var(--font-button);
}

:focus-visible {
  outline: 2px solid var(--color-ink);
  outline-offset: 2px;
}
</style>
