<script setup lang="ts">
import {
  Map as MapLibreMap,
  setWorkerUrl,
  type GeoJSONSource,
  type VectorTileSource,
} from 'maplibre-gl'
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url'
import 'maplibre-gl/dist/maplibre-gl.css'
import { computed, onMounted, onUnmounted, ref, useTemplateRef, watch } from 'vue'

import PipeSetSelector from '@/components/PipeSetSelector.vue'
import PipeSidebar from '@/components/PipeSidebar.vue'
import { usePipeSetsQuery } from '@/composables/usePipeSetsQuery'
import type { District, Prefecture } from '@/services'

defineOptions({ name: 'PipeMap' })

const osmAttribution =
  '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
const sidebarOpen = ref(true)
const container = useTemplateRef<HTMLDivElement>('container')
const { sets, loading, failed, load } = usePipeSetsQuery()
const selectedId = ref('')
const selectedSet = computed(() => sets.value.find(({ id }) => id === selectedId.value))
let map: MapLibreMap | undefined
let mapReady = false
let areaBounds: [number, number, number, number] | null = null

const refreshPipeSets = async (preferredId?: string) => {
  const result = await load()
  if (!result) return

  const target = preferredId ?? selectedId.value
  selectedId.value = result.find(({ id }) => id === target)?.id ?? result[0]?.id ?? ''
}

const selectGeneratedPipeSet = (id: string) => {
  void refreshPipeSets(id)
}

const fitMapBounds = (bounds: [number, number, number, number]) => {
  if (!map) return

  const layout = container.value?.parentElement
  const sidebar = layout?.querySelector('aside')?.getBoundingClientRect()
  const sidebarRight = sidebar?.right ?? 0
  const controlsBottom = Math.max(
    sidebar?.bottom ?? 0,
    layout?.querySelector('.selector')?.getBoundingClientRect().bottom ?? 0,
  )
  const width = container.value?.clientWidth ?? 0
  const height = container.value?.clientHeight ?? 0

  if (width - sidebarRight >= 360) {
    map.fitBounds(bounds, {
      padding: { top: 48, right: 48, bottom: 48, left: sidebarRight + 48 },
    })
  } else {
    const padding =
      height - controlsBottom >= 150
        ? { top: controlsBottom + 24, right: 48, bottom: 48, left: 48 }
        : 48
    map.fitBounds(bounds, { padding })
  }
}

const showPipeSet = () => {
  if (!map || !mapReady || !selectedId.value) return

  const id = selectedId.value
  const [west, south, east, north] = selectedSet.value?.bounds ?? []
  if (west !== undefined && south !== undefined && east !== undefined && north !== undefined) {
    fitMapBounds([west, south, east, north])
  }

  const tiles = [
    `${window.location.origin}/tiles/pipes/{z}/{x}/{y}?pipeset_id=${encodeURIComponent(id)}`,
  ]
  const source = map.getSource<VectorTileSource>('pipes')

  if (source) {
    source.setTiles(tiles)
    return
  }

  map.addSource('pipes', { type: 'vector', tiles, attribution: osmAttribution })
  map.addLayer({
    id: 'pipes',
    type: 'line',
    source: 'pipes',
    'source-layer': 'pipes',
    paint: { 'line-color': '#17608a', 'line-width': 2 },
  })
}

watch(selectedId, showPipeSet)

const showAreaBounds = () => {
  const source = map?.getSource<GeoJSONSource>('district-bounds')
  if (!source) return

  if (!areaBounds) {
    source.setData({ type: 'FeatureCollection', features: [] })
    return
  }

  const [west, south, east, north] = areaBounds
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

const selectArea = (area: District | Prefecture | null) => {
  const [west, south, east, north] = area?.bounds ?? []
  areaBounds =
    west !== undefined && south !== undefined && east !== undefined && north !== undefined
      ? [west, south, east, north]
      : null

  showAreaBounds()

  if (areaBounds) fitMapBounds(areaBounds)
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
      ],
    },
  })

  map.once('style.load', () => {
    mapReady = true
    showAreaBounds()
    showPipeSet()
  })

  void refreshPipeSets()
})

onUnmounted(() => map?.remove())
</script>

<template>
  <div class="map-layout">
    <div ref="container" class="map-canvas"></div>
    <div class="map-tools">
      <PipeSetSelector
        v-model="selectedId"
        class="selector"
        :sets="sets"
        :loading="loading"
        :failed="failed"
      />
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

.map-canvas {
  position: absolute;
  inset: 0;
  z-index: 0;
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

.selector {
  grid-area: 1 / 2;
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

  .selector {
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
