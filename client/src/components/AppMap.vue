<script setup lang="ts">
import { onMounted, onUnmounted, useTemplateRef } from 'vue'
import { Map } from 'mapbox-gl/esm'
import { useDrawing } from '@/composables/useDrawing'
import 'mapbox-gl/dist/mapbox-gl.css'

const { initializeDrawing, disposeDrawing } = useDrawing()
const mapRef = useTemplateRef<HTMLDivElement>('mapRef')
let map: Map | undefined

onMounted(() => {
  const mapInstance = new Map({
    container: mapRef.value!,
    accessToken: import.meta.env.VITE_MAPBOX_ACCESS_TOKEN,
    style: 'mapbox://styles/mapbox/streets-v12',
  })
  map = mapInstance

  mapInstance.once('load', () => {
    initializeDrawing(mapInstance)
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
