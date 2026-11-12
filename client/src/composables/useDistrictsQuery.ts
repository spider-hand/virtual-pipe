import { onScopeDispose, ref, shallowRef } from 'vue'

import { Configuration, DistrictsApi, type District } from '@/services'

const api = new DistrictsApi(new Configuration({ basePath: '' }))

export const useDistrictsQuery = () => {
  const results = shallowRef<District[]>([])
  const loading = ref(false)
  const unavailable = ref(false)
  let timer: ReturnType<typeof setTimeout> | undefined
  let request: AbortController | undefined

  const clear = () => {
    clearTimeout(timer)
    request?.abort()
    results.value = []
    loading.value = false
    unavailable.value = false
  }

  const search = (text: string) => {
    clear()

    const q = text.trim()
    if (!q) return

    loading.value = true
    const pending = new AbortController()
    request = pending

    timer = setTimeout(async () => {
      try {
        const districts = await api.searchDistricts({ q }, { signal: pending.signal })
        if (!pending.signal.aborted) results.value = districts
      } catch {
        if (!pending.signal.aborted) unavailable.value = true
      } finally {
        if (!pending.signal.aborted) loading.value = false
      }
    }, 200)
  }

  onScopeDispose(clear)

  return { results, loading, unavailable, search, clear }
}
