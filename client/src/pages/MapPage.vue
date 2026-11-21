<script setup lang="ts">
import { computed, onMounted, ref, shallowRef, useTemplateRef } from 'vue'

import Map from '@/components/Map.vue'
import PipeSetSelector from '@/components/PipeSetSelector.vue'
import PipeSidebar from '@/components/PipeSidebar.vue'
import RoadDataStatus from '@/components/RoadDataStatus.vue'
import { usePipeSetsQuery } from '@/composables/usePipeSetsQuery'
import type { District, Prefecture } from '@/services'

defineOptions({ name: 'MapPage' })

const mapTools = useTemplateRef<HTMLDivElement>('mapTools')

const topControls = useTemplateRef<HTMLDivElement>('topControls')

const sidebarOpen = ref(true)

const { pipeSets, isPipeSetsFetching, isPipeSetsError, loadPipeSets } = usePipeSetsQuery()

const selectedId = ref('')
const selectedSet = computed(() => pipeSets.value.find(({ id }) => id === selectedId.value))

const areaBounds = shallowRef<number[] | null>(null)

const refreshPipeSets = async (preferredId?: string) => {
  const result = await loadPipeSets()
  if (!result) return

  const target = preferredId ?? selectedId.value
  selectedId.value = result.find(({ id }) => id === target)?.id ?? result[0]?.id ?? ''
}

const selectGeneratedPipeSet = (id: string) => {
  void refreshPipeSets(id)
}

const getFitPadding = (width: number, height: number) => {
  const sidebar = mapTools.value?.querySelector('aside')?.getBoundingClientRect()
  const sidebarRight = sidebar?.right ?? 0
  const topControlsBottom = topControls.value?.getBoundingClientRect().bottom ?? 0

  const fitsBesideSidebar = width - sidebarRight >= 360
  const controlsBottom = fitsBesideSidebar
    ? topControlsBottom
    : Math.max(sidebar?.bottom ?? 0, topControlsBottom)
  const top = height - controlsBottom >= 112 ? Math.max(48, controlsBottom + 24) : 48

  return fitsBesideSidebar
    ? { top, right: 48, bottom: 48, left: sidebarRight + 48 }
    : top > 48
      ? { top, right: 48, bottom: 48, left: 48 }
      : 48
}

const selectArea = (area: District | Prefecture | null) => {
  areaBounds.value = area?.bounds ?? null
}

onMounted(() => {
  void refreshPipeSets()
})
</script>

<template>
  <div class="map-layout">
    <Map
      :pipe-set-id="selectedId"
      :pipe-set-bounds="selectedSet?.bounds ?? null"
      :area-bounds="areaBounds"
      :get-fit-padding="getFitPadding"
    />
    <div ref="mapTools" class="map-tools">
      <div ref="topControls" class="top-controls">
        <RoadDataStatus />
        <PipeSetSelector
          v-model="selectedId"
          class="selector"
          :sets="pipeSets"
          :loading="isPipeSetsFetching"
          :failed="isPipeSetsError"
        />
      </div>
      <PipeSidebar
        v-model:open="sidebarOpen"
        class="pipe-tools"
        :selected-set="selectedSet"
        @area-change="selectArea"
        @pipeset-ready="selectGeneratedPipeSet"
      />
    </div>
  </div>
</template>

<style scoped>
.map-layout {
  position: fixed;
  inset: 0;
}

.map-tools {
  position: absolute;
  inset: var(--space-md);
  z-index: 2;
  display: grid;
  grid-template-columns: minmax(0, 392px) minmax(0, 264px);
  grid-template-rows: minmax(0, 1fr);
  justify-content: space-between;
  align-items: start;
  gap: var(--space-sm);
  pointer-events: none;
}

.top-controls {
  grid-area: 1 / 2;
  display: grid;
  gap: var(--space-xs);
}

.top-controls > * {
  pointer-events: auto;
}

.pipe-tools {
  grid-area: 1 / 1;
}

@media (max-width: 700px) {
  .map-tools {
    grid-template-columns: minmax(0, 1fr);
    grid-template-rows: auto minmax(0, 1fr);
  }

  .top-controls {
    grid-area: 1 / 1;
    justify-self: end;
    width: min(100%, 264px);
  }

  .pipe-tools {
    grid-area: 2 / 1;
    width: min(100%, 392px);
    max-height: min(100%, 45dvh);
  }
}
</style>
