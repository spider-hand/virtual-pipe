<script setup lang="ts">
import { ArrowLeft, LoaderCircle } from '@lucide/vue'
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { RouterLink } from 'vue-router'

import FormField from '@/components/FormField.vue'
import SelectField from '@/components/SelectField.vue'
import { useRoadDataQuery } from '@/composables/useRoadDataQuery'
import type { RoadDataRegionEnum } from '@/services'

const { t } = useI18n()
const { data, isError, submit, submitting, submitError, active } = useRoadDataQuery()
const region = ref<RoadDataRegionEnum | ''>('')
const setup = computed(() => data.value?.setup)
const busy = computed(() => active.value || submitting.value)
const selectedIsActive = computed(() => region.value === data.value?.activeRegion)
const canPrepare = computed(() => !!region.value && !busy.value && !selectedIsActive.value)
const actionLabel = computed(() => {
  if (selectedIsActive.value) return t('pages.RoadDataSetupPage.alreadyActive')

  return region.value && data.value?.cachedRegions.includes(region.value)
    ? t('pages.RoadDataSetupPage.activate')
    : t('pages.RoadDataSetupPage.download')
})
const regionLabel = (value: RoadDataRegionEnum) => t(`pages.RoadDataSetupPage.regions.${value}`)
const options = computed(() => [
  { value: '' as const, label: t('pages.RoadDataSetupPage.selectRegion'), disabled: true },
  ...(data.value?.regions ?? []).map((value) => ({ value, label: regionLabel(value) })),
])

const coverage = computed(() => {
  if (data.value?.activeRegion) {
    return t('pages.RoadDataSetupPage.activeRegion', {
      region: regionLabel(data.value.activeRegion),
    })
  }

  if (data.value) {
    return t(`pages.RoadDataSetupPage.${data.value.hasRoads ? 'unknownRegion' : 'noRoads'}`)
  }

  return t(`pages.RoadDataSetupPage.${isError.value ? 'coverageError' : 'loadingCoverage'}`)
})

const setupMessage = computed(() => {
  if (active.value && setup.value) {
    return t(`pages.RoadDataSetupPage.status.${setup.value.status}`, {
      region: regionLabel(setup.value.region),
    })
  }

  if (submitting.value) return t('pages.RoadDataSetupPage.status.submitting')
  if (submitError.value) return t(`pages.RoadDataSetupPage.errors.${submitError.value}`)
  if (setup.value?.status === 'failed') {
    return t(`pages.RoadDataSetupPage.errors.${setup.value.failure ?? 'submitFailed'}`, {
      region: regionLabel(setup.value.region),
    })
  }

  return ''
})

watch(
  setup,
  (job) => {
    if (job && (active.value || (job.status === 'failed' && !region.value))) {
      region.value = job.region
    }
  },
  { immediate: true },
)

const prepare = () => {
  if (region.value && canPrepare.value) submit(region.value)
}
</script>

<template>
  <main class="road-data-setup">
    <div class="content">
      <RouterLink class="back-link" :to="{ name: 'map' }">
        <ArrowLeft :size="16" aria-hidden="true" />
        {{ t('pages.RoadDataSetupPage.back') }}
      </RouterLink>

      <h1>{{ t('pages.RoadDataSetupPage.title') }}</h1>

      <section class="coverage" aria-labelledby="road-data-coverage-heading">
        <h2 id="road-data-coverage-heading">{{ t('pages.RoadDataSetupPage.coverage') }}</h2>
        <p role="status">{{ coverage }}</p>
      </section>

      <form class="prepare" @submit.prevent="prepare">
        <FormField class="region-field" :label="t('pages.RoadDataSetupPage.region')">
          <SelectField v-model="region" :options="options" :disabled="!data || busy" />
        </FormField>
        <button type="submit" :disabled="!canPrepare">
          {{ actionLabel }}
        </button>
        <p class="setup-status" role="status">
          <LoaderCircle v-if="busy" class="spinner" :size="16" aria-hidden="true" />
          {{ setupMessage }}
        </p>
      </form>
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
  background: var(--color-primary);
  color: var(--color-on-primary);
  font: var(--font-button);
  cursor: pointer;
}

button:enabled:active {
  background: var(--color-primary-active);
}

button:disabled {
  background: var(--color-primary-disabled);
  color: var(--color-muted);
  cursor: default;
}

.setup-status {
  font: var(--font-body-sm);
  display: flex;
  align-items: center;
  gap: var(--space-xs);
}

.spinner {
  flex: none;
}

@media (prefers-reduced-motion: no-preference) {
  .spinner {
    animation: spin 1s linear infinite;
  }
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

:focus-visible {
  outline: 2px solid var(--color-ink);
  outline-offset: 2px;
}
</style>
