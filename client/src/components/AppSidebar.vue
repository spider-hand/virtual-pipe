<script setup lang="ts">
import { useForm } from 'vee-validate'
import { ResponseError } from '@/services'
import { PencilSparkles } from '@lucide/vue'
import { useDrawing } from '@/composables/useDrawing'
import { usePipesetAPI } from '@/composables/usePipesetAPI'

const { isMapReady, hasBbox, isDrawing, bbox, startDrawing, resetBbox } = useDrawing()
const { createPipeset } = usePipesetAPI()

type PipesetForm = {
  name: string
  count: number | ''
  bbox: number[] | null
}

const { defineField, handleSubmit, setFieldValue } = useForm<PipesetForm>({
  initialValues: { name: '', count: 1, bbox: null },
  validationSchema: {
    name: (value: unknown) =>
      (typeof value === 'string' && value.trim().length > 0) || 'Name is required.',
    count: (value: unknown) =>
      (typeof value === 'number' && Number.isInteger(value) && value >= 1) ||
      'Count must be an integer greater than or equal to 1.',
    bbox: (value: unknown) => {
      if (!Array.isArray(value) || value.length !== 4 || !value.every(Number.isFinite)) {
        return 'Select a bbox with four finite coordinates.'
      }
      const [west, south, east, north] = value as [number, number, number, number]
      if (west < -180 || west > 180 || east < -180 || east > 180) {
        return 'Longitude must be between -180 and 180.'
      }
      if (south < -90 || south > 90 || north < -90 || north > 90) {
        return 'Latitude must be between -90 and 90.'
      }
      return (
        (west < east && south < north) || 'West must be less than east and south less than north.'
      )
    },
  },
})
const [name] = defineField('name')
const [count] = defineField('count')

const submitForm = handleSubmit(
  async (values) => {
    try {
      return await createPipeset({
        name: values.name.trim(),
        count: Number(values.count),
        bbox: values.bbox!,
      })
    } catch (error) {
      if (error instanceof ResponseError) {
        console.error(await error.response.text())
      } else {
        console.error(error)
      }
    }
  },
  ({ errors }) => console.error(errors),
)

const submit = (event: Event) => {
  setFieldValue('bbox', bbox.value ? [...bbox.value] : null, false)
  return submitForm(event)
}

const handleClick = () => {
  if (isDrawing.value || hasBbox.value) resetBbox()
  else startDrawing()
}
</script>

<template>
  <aside class="sidebar">
    <form novalidate @submit="submit">
      <div>
        <label for="pipeset-name">Pipeset name</label>
        <input id="pipeset-name" v-model="name" type="text" />
      </div>
      <div>
        <label for="pipe-count">Pipe count</label>
        <input id="pipe-count" v-model.number="count" type="number" min="1" step="1" />
      </div>
      <button type="submit">Submit pipeset</button>
    </form>
    <button type="button" :disabled="!isMapReady" @click="handleClick">
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
