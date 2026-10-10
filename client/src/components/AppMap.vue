<script setup lang="ts">
import { onMounted, onUnmounted, ref, useTemplateRef, watch } from 'vue'
import { Map } from 'mapbox-gl/esm'
import { useDrawing } from '@/composables/useDrawing'
import { usePipeset } from '@/composables/usePipeset'
import 'mapbox-gl/dist/mapbox-gl.css'

const { initializeDrawing, disposeDrawing } = useDrawing()
const { pipesetId } = usePipeset()
const isLoaded = ref(false)
const mapRef = useTemplateRef<HTMLDivElement>('mapRef')
let map: Map | undefined

watch([pipesetId, isLoaded], ([pipesetId, loaded]) => {
  if (!loaded || pipesetId === undefined || !map) return
  if (map.getLayer('pipes')) map.removeLayer('pipes')
  if (map.getSource('pipes')) map.removeSource('pipes')
  map.addSource('pipes', {
    type: 'vector',
    tiles: [`${window.location.origin}/tiles/pipes/{z}/{x}/{y}?pipeset_id=${pipesetId}`],
    attribution:
      '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
  })
  map.addLayer({
    id: 'pipes',
    type: 'line',
    source: 'pipes',
    'source-layer': 'pipes',
    paint: { 'line-color': '#2563eb', 'line-width': 3 },
  })
})

onMounted(() => {
  const mapInstance = new Map({
    container: mapRef.value!,
    accessToken: import.meta.env.VITE_MAPBOX_ACCESS_TOKEN,
    style: 'mapbox://styles/mapbox/streets-v12',
  })
  map = mapInstance

  mapInstance.once('load', () => {
    initializeDrawing(mapInstance)
    isLoaded.value = true
  })
})

onUnmounted(() => {
  disposeDrawing()
  map?.remove()
})
</script>

<template>
  <div ref="mapRef" class="map" />
</template>

<style scoped>
.map {
  width: 100%;
  height: 100%;
}
</style>
