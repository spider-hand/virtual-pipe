<script setup lang="ts">
import { PencilSparkles } from '@lucide/vue'
import { useDrawing } from '@/composables/useDrawing'
import { usePipeset } from '@/composables/usePipeset'

const { isMapReady, hasBbox, isDrawing, startDrawing, resetBbox } = useDrawing()
const { name, count } = usePipeset()

const handleClick = () => {
  if (isDrawing.value || hasBbox.value) resetBbox()
  else startDrawing()
}
</script>

<template>
  <aside class="sidebar">
    <div>
      <label for="pipeset-name">Pipeset name</label>
      <input id="pipeset-name" v-model="name" type="text" />
    </div>
    <div>
      <label for="pipe-count">Pipe count</label>
      <input id="pipe-count" v-model.number="count" type="number" min="1" step="1" />
    </div>
    <button type="button" :disabled="!isMapReady" @click="handleClick">
      <PencilSparkles aria-hidden="true" />
      {{ isDrawing ? 'Cancel drawing' : hasBbox ? 'Reset bbox' : 'Start drawing' }}
    </button>
  </aside>
</template>

<style scoped>
.sidebar {
  width: 360px;
  flex-shrink: 0;
}
</style>
