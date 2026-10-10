<script setup lang="ts">
import { PencilSparkles } from '@lucide/vue'
import { useDrawing } from '@/composables/useDrawing'

const { isMapReady, hasBbox, isDrawing, startDrawing, resetBbox } = useDrawing()

const handleClick = () => {
  if (isDrawing.value || hasBbox.value) resetBbox()
  else startDrawing()
}
</script>

<template>
  <aside class="sidebar">
    <button
      type="button"
      :disabled="!isMapReady"
      @click="handleClick"
    >
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
