import { ref } from 'vue'
import { useQuery, useQueryClient } from '@tanstack/vue-query'
import { Configuration, PipesetsApi, type Pipeset } from '@/services'

const pipesetId = ref<number>()

export const usePipeset = () => {
  const api = new PipesetsApi(new Configuration({ basePath: '' }))
  const queryClient = useQueryClient()
  const { data: pipeset } = useQuery({
    queryKey: ['pipeset', pipesetId],
    queryFn: () => api.getPipeset({ pipesetId: pipesetId.value! }),
    enabled: () => pipesetId.value !== undefined,
    staleTime: Infinity,
    retry: false,
  })

  const createPipeset = (pipeset: Pipeset) => api.createPipeset({ pipeset })
  const getPipeset = (pipesetId: number) =>
    queryClient.fetchQuery({
      queryKey: ['pipeset', pipesetId],
      queryFn: () => api.getPipeset({ pipesetId }),
      staleTime: 0,
      retry: false,
    })

  return { pipesetId, pipeset, createPipeset, getPipeset }
}
