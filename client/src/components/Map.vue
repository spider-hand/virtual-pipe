<script setup lang="ts">
import { Map as MapLibreMap, setWorkerUrl } from 'maplibre-gl'
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url'
import 'maplibre-gl/dist/maplibre-gl.css'
import { onMounted, onUnmounted, useTemplateRef } from 'vue'

import DistrictSearch from '@/components/DistrictSearch.vue'
import type { District } from '@/services'

defineOptions({ name: 'PipeMap' })

const pipesetId = '00000000-0000-4000-8000-000000000001'
const osmAttribution =
  '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
const container = useTemplateRef<HTMLDivElement>('container')
let map: MapLibreMap | undefined

const fitDistrict = ({ bounds }: District) => {
  const [west, south, east, north] = bounds
  if (west === undefined || south === undefined || east === undefined || north === undefined) return

  map?.fitBounds([west, south, east, north], { padding: 48 })
}

onMounted(() => {
  if (!container.value) return

  setWorkerUrl(workerUrl)

  map = new MapLibreMap({
    container: container.value,
    center: [134.0466, 34.3447],
    zoom: 13,
    style: {
      version: 8,
      sources: {
        basemap: {
          type: 'raster',
          tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
          tileSize: 256,
          maxzoom: 19,
          attribution: osmAttribution,
        },
        pipes: {
          type: 'vector',
          tiles: [`${window.location.origin}/tiles/pipes/{z}/{x}/{y}?pipeset_id=${pipesetId}`],
          attribution: osmAttribution,
        },
      },
      layers: [
        {
          id: 'background',
          type: 'background',
          paint: { 'background-color': '#f5f5f5' },
        },
        {
          id: 'basemap',
          type: 'raster',
          source: 'basemap',
          paint: { 'raster-saturation': -0.45 },
        },
        {
          id: 'pipes',
          type: 'line',
          source: 'pipes',
          'source-layer': 'pipes',
          paint: { 'line-color': '#17608a', 'line-width': 2 },
        },
      ],
    },
  })
})

onUnmounted(() => map?.remove())
</script>

<template>
  <div class="map-layout">
    <DistrictSearch @select="fitDistrict" />
    <div ref="container"></div>
  </div>
</template>

<style scoped>
.map-layout {
  display: grid;
  grid-template-rows: auto minmax(0, 1fr);
  position: fixed;
  inset: 0;
}
</style>
