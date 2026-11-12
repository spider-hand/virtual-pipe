import { shallowRef } from 'vue'

import { Configuration, HealthApi, type HealthResponse } from '@/services'

// Use the current origin so Vite can proxy /api requests to Django.
const healthApi = new HealthApi(new Configuration({ basePath: '' }))

export const useHealthQuery = () => {
  const data = shallowRef<HealthResponse>()
  const error = shallowRef<unknown>()

  const checkHealth = async () => {
    data.value = undefined
    error.value = undefined

    try {
      data.value = await healthApi.getHealth()
    } catch (cause) {
      error.value = cause
    }
  }

  return { data, error, checkHealth }
}
