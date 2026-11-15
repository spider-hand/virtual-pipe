import { onScopeDispose, ref, shallowRef } from 'vue'

import { Configuration, PipesetsApi, type PipeSetSummary } from '@/services'

const api = new PipesetsApi(new Configuration({ basePath: '' }))

export const usePipeSetsQuery = () => {
  const sets = shallowRef<PipeSetSummary[]>([])
  const loading = ref(false)
  const failed = ref(false)
  let controller: AbortController | undefined

  const load = async () => {
    controller?.abort()
    controller = new AbortController()
    const { signal } = controller

    loading.value = true
    failed.value = false

    try {
      const result = await api.listPipeSets({ signal })
      if (signal.aborted) return

      sets.value = result
      return result
    } catch {
      if (!signal.aborted) failed.value = true
    } finally {
      if (!signal.aborted) loading.value = false
    }
  }

  onScopeDispose(() => controller?.abort())

  return { sets, loading, failed, load }
}
