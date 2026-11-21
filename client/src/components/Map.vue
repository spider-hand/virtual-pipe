<script setup lang="ts">
import {
  Map as MapLibreMap,
  setWorkerUrl,
  type GeoJSONSource,
  type PaddingOptions,
  type VectorTileSource,
} from 'maplibre-gl'
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url'
import 'maplibre-gl/dist/maplibre-gl.css'
import { onMounted, onUnmounted, useTemplateRef, watch } from 'vue'

defineOptions({ name: 'PipeMap' })

type Bounds = [number, number, number, number]

const props = defineProps<{
  pipeSetId: string
  pipeSetBounds: number[] | null
  areaBounds: number[] | null
  getFitPadding: (width: number, height: number) => number | PaddingOptions
}>()

const container = useTemplateRef<HTMLDivElement>('container')

const osmAttribution =
  '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'

let map: MapLibreMap | undefined
let mapReady = false

const readBounds = (bounds: number[] | null): Bounds | null => {
  const [west, south, east, north] = bounds ?? []
  if (west === undefined || south === undefined || east === undefined || north === undefined) {
    return null
  }

  return [west, south, east, north]
}

const fitMapBounds = (bounds: Bounds) => {
  if (!map || !container.value) return

  const { clientWidth, clientHeight } = container.value
  map.fitBounds(bounds, { padding: props.getFitPadding(clientWidth, clientHeight) })
}

const showPipeSet = () => {
  if (!map || !mapReady || !props.pipeSetId) return

  const id = props.pipeSetId
  const bounds = readBounds(props.pipeSetBounds)
  if (bounds) fitMapBounds(bounds)

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

watch(() => props.pipeSetId, showPipeSet)

const showAreaBounds = (bounds: Bounds | null) => {
  const source = map?.getSource<GeoJSONSource>('district-bounds')
  if (!source) return

  if (!bounds) {
    source.setData({ type: 'FeatureCollection', features: [] })
    return
  }

  const [west, south, east, north] = bounds
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

watch(
  () => props.areaBounds,
  (value) => {
    const bounds = readBounds(value)
    showAreaBounds(bounds)

    if (bounds) fitMapBounds(bounds)
  },
)

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
    showAreaBounds(readBounds(props.areaBounds))
    showPipeSet()
  })
})

onUnmounted(() => map?.remove())
</script>

<template>
  <div ref="container" class="map-canvas"></div>
</template>

<style scoped>
.map-canvas {
  position: absolute;
  inset: 0;
  z-index: 0;
}
</style>
