import { Configuration, PipesetsApi, type Pipeset } from '@/services'

export const usePipesetAPI = () => {
  const api = new PipesetsApi(new Configuration({ basePath: '' }))

  const createPipeset = (pipeset: Pipeset) => api.createPipeset({ pipeset })

  return { createPipeset }
}
