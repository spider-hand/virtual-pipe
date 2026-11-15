<script setup lang="ts">
import { Map as MapLibreMap, setWorkerUrl, type GeoJSONSource } from 'maplibre-gl'
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url'
import 'maplibre-gl/dist/maplibre-gl.css'
import { onMounted, onUnmounted, ref, useTemplateRef } from 'vue'

import PipeSidebar from '@/components/PipeSidebar.vue'
import type { District } from '@/services'

defineOptions({ name: 'PipeMap' })

const pipesetId = '00000000-0000-4000-8000-000000000001'
const osmAttribution =
  '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
const sidebarOpen = ref(true)
const container = useTemplateRef<HTMLDivElement>('container')
let map: MapLibreMap | undefined
let districtBounds: [number, number, number, number] | null = null

const showDistrictBounds = () => {
  const source = map?.getSource<GeoJSONSource>('district-bounds')
  if (!source) return

  if (!districtBounds) {
    source.setData({ type: 'FeatureCollection', features: [] })
    return
  }

  const [west, south, east, north] = districtBounds
  source.setData({
    type: 'Polygon',
    coordinates: [
      [
        [west, south],
        [east, south],
        [east, north],
        [west, north],
        [west, south],
      ],
    ],
  })
}

const selectDistrict = (district: District | null) => {
  const [west, south, east, north] = district?.bounds ?? []
  districtBounds =
    west !== undefined && south !== undefined && east !== undefined && north !== undefined
      ? [west, south, east, north]
      : null

  showDistrictBounds()

  if (districtBounds && map) {
    const sidebar = container.value?.parentElement?.querySelector('aside')
    const sidebarWidth = sidebar?.getBoundingClientRect().right ?? 0
    const width = container.value?.clientWidth ?? 0
    const padding =
      width - sidebarWidth >= 360 ? { top: 48, right: 48, bottom: 48, left: sidebarWidth + 48 } : 48

    map.fitBounds(districtBounds, { padding })
  }
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
        'district-bounds': {
          type: 'geojson',
          data: { type: 'FeatureCollection', features: [] },
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
          id: 'district-bounds-fill',
          type: 'fill',
          source: 'district-bounds',
          paint: { 'fill-color': '#17608a', 'fill-opacity': 0.12 },
        },
        {
          id: 'district-bounds-outline',
          type: 'line',
          source: 'district-bounds',
          paint: { 'line-color': '#17608a', 'line-width': 2, 'line-dasharray': [3, 2] },
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

  map.once('load', showDistrictBounds)
})

onUnmounted(() => map?.remove())
</script>

<template>
  <div class="map-layout">
    <PipeSidebar v-model:open="sidebarOpen" @district-change="selectDistrict" />
    <div ref="container" class="map-canvas"></div>
  </div>
</template>

<style scoped>
.map-layout {
  position: fixed;
  inset: 0;
}

.map-canvas {
  position: absolute;
  inset: 0;
  z-index: 0;
}
</style>
