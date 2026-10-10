<script setup lang="ts">
import { onMounted, onUnmounted, useTemplateRef } from 'vue'
import { Map } from 'mapbox-gl/esm'
import 'mapbox-gl/dist/mapbox-gl.css'

const mapRef = useTemplateRef<HTMLDivElement>('mapRef')
let map: Map | undefined

onMounted(() => {
  map = new Map({
    container: mapRef.value!,
    accessToken: import.meta.env.VITE_MAPBOX_ACCESS_TOKEN,
    style: 'mapbox://styles/mapbox/streets-v12',
  })
})

onUnmounted(() => {
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
