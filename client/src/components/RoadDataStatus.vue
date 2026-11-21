<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { RouterLink } from 'vue-router'

import { useRoadDataQuery } from '@/composables/useRoadDataQuery'

const { t } = useI18n()

const { roadData, isRoadDataError } = useRoadDataQuery()

const regionStatus = computed(() => {
  if (roadData.value?.activeRegion) {
    return t(`components.RoadDataStatus.regions.${roadData.value.activeRegion}`)
  }

  if (roadData.value) {
    return t(`components.RoadDataStatus.${roadData.value.hasRoads ? 'unknownRegion' : 'noRoads'}`)
  }

  return t(`components.RoadDataStatus.${isRoadDataError.value ? 'unavailable' : 'loading'}`)
})
</script>

<template>
  <section class="road-data" aria-labelledby="road-data-heading">
    <div class="road-data-status">
      <h2 id="road-data-heading">{{ t('components.RoadDataStatus.roadDataRegion') }}</h2>
      <p role="status">{{ regionStatus }}</p>
    </div>
    <RouterLink :to="{ name: 'setup' }">
      {{ t('components.RoadDataStatus.manageRoadData') }}
    </RouterLink>
  </section>
</template>

<style scoped>
.road-data {
  box-sizing: border-box;
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  justify-content: space-between;
  gap: var(--space-xxs) var(--space-sm);
  padding: var(--space-xs);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-lg);
  background: var(--color-canvas);
  color: var(--color-ink);
}

.road-data-status h2 {
  margin: 0;
  color: var(--color-muted);
  font: var(--font-caption);
}

.road-data-status p {
  margin: 0;
  font: var(--font-body-md);
}

.road-data a {
  display: inline-flex;
  min-height: 44px;
  align-items: flex-end;
  color: inherit;
  font: var(--font-nav-link);
  text-underline-offset: 3px;
}

.road-data a:focus-visible {
  outline: 2px solid var(--color-ink);
  outline-offset: 2px;
}
</style>
