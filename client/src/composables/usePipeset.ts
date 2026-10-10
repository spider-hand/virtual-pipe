import { ref } from 'vue'
import { Configuration, PipesetsApi, type Pipeset } from '@/services'

const pipesetId = ref<number>()

export const usePipeset = () => {
  const api = new PipesetsApi(new Configuration({ basePath: '' }))

  const createPipeset = (pipeset: Pipeset) => api.createPipeset({ pipeset })
  const getPipeset = (pipesetId: number) => api.getPipeset({ pipesetId })

  return { pipesetId, createPipeset, getPipeset }
}
