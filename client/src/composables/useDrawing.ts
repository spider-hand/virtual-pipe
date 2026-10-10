import { computed, readonly, ref } from 'vue'
import type { Map } from 'mapbox-gl/esm'
import { TerraDraw, TerraDrawRectangleMode } from 'terra-draw'
import { TerraDrawMapboxGLAdapter } from 'terra-draw-mapbox-gl-adapter'

const isMapReady = ref(false)
const isDrawing = ref(false)
const bbox = ref<[number, number, number, number] | null>(null)
const hasBbox = computed(() => bbox.value !== null)
let draw: TerraDraw | undefined

const initializeDrawing = (map: Map) => {
  const drawing = new TerraDraw({
    adapter: new TerraDrawMapboxGLAdapter({ map }),
    modes: [new TerraDrawRectangleMode({ drawInteraction: 'click-move' })],
  })
  draw = drawing

  drawing.on('ready', () => {
    isMapReady.value = true
  })
  drawing.on('finish', (id) => {
    const feature = drawing.getSnapshotFeature(id)
    if (feature?.geometry.type !== 'Polygon') return

    const coordinates: number[][] = feature.geometry.coordinates[0]!
    const longitudes = coordinates.map(([longitude]) => longitude!)
    const latitudes = coordinates.map(([, latitude]) => latitude!)
    bbox.value = [
      Math.min(...longitudes),
      Math.min(...latitudes),
      Math.max(...longitudes),
      Math.max(...latitudes),
    ]

    drawing.setMode('static')
    isDrawing.value = false
  })

  drawing.start()
}

const disposeDrawing = () => {
  draw?.stop()
  draw = undefined
  isMapReady.value = false
  isDrawing.value = false
  bbox.value = null
}

const resetBbox = () => {
  if (!draw) return

  draw.setMode('static')
  draw.clear()
  isDrawing.value = false
  bbox.value = null
}

const startDrawing = () => {
  if (!draw) return

  resetBbox()
  draw.setMode('rectangle')
  isDrawing.value = true
}

export const useDrawing = () => {
  return {
    isMapReady: readonly(isMapReady),
    isDrawing: readonly(isDrawing),
    hasBbox: readonly(hasBbox),
    bbox: readonly(bbox),
    initializeDrawing,
    disposeDrawing,
    startDrawing,
    resetBbox,
  }
}
