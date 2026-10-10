import { readonly, ref } from 'vue'
import type { Map } from 'mapbox-gl/esm'
import { TerraDraw, TerraDrawRectangleMode } from 'terra-draw'
import { TerraDrawMapboxGLAdapter } from 'terra-draw-mapbox-gl-adapter'

const isMapReady = ref(false)
const isDrawing = ref(false)
const hasBbox = ref(false)
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
    const bbox = [
      Math.min(...longitudes),
      Math.min(...latitudes),
      Math.max(...longitudes),
      Math.max(...latitudes),
    ]

    console.log(bbox)
    drawing.setMode('static')
    isDrawing.value = false
    hasBbox.value = true
  })

  drawing.start()
}

const disposeDrawing = () => {
  draw?.stop()
  draw = undefined
  isMapReady.value = false
  isDrawing.value = false
  hasBbox.value = false
}

const resetBbox = () => {
  if (!draw) return

  draw.setMode('static')
  draw.clear()
  isDrawing.value = false
  hasBbox.value = false
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
    initializeDrawing,
    disposeDrawing,
    startDrawing,
    resetBbox,
  }
}
