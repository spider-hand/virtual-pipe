import { useQuery, useQueryClient } from '@tanstack/vue-query'
import { computed } from 'vue'

import { Configuration, HealthApi } from '@/services'

const api = new HealthApi(new Configuration({ basePath: '' }))

const healthKey = ['health'] as const

export const useHealthQuery = () => {
  const client = useQueryClient()

  const { data, error, refetch } = useQuery({
    queryKey: healthKey,
    queryFn: ({ signal }) => api.getHealth({ signal }),
    enabled: false,
  })

  const checkHealth = async () => {
    await client.resetQueries({ queryKey: healthKey })
    await refetch()
  }

  return { health: data, healthError: computed(() => error.value ?? undefined), checkHealth }
}
