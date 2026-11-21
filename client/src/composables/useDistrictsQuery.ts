import { useQuery } from '@tanstack/vue-query'
import { computed, onScopeDispose, ref } from 'vue'

import { Configuration, DistrictsApi } from '@/services'

const api = new DistrictsApi(new Configuration({ basePath: '' }))
const districtsKey = ['districts'] as const

export const useDistrictsQuery = () => {
  const term = ref('')
  const debouncing = ref(false)
  let timer: ReturnType<typeof setTimeout> | undefined

  const { data, isFetching, isError } = useQuery({
    queryKey: computed(() => [...districtsKey, term.value] as const),
    queryFn: ({ queryKey: [, q], signal }) => api.searchDistricts({ q }, { signal }),
    enabled: computed(() => Boolean(term.value)),
  })

  const clear = () => {
    clearTimeout(timer)
    term.value = ''
    debouncing.value = false
  }

  const search = (text: string) => {
    clear()

    const q = text.trim()
    if (!q) return

    debouncing.value = true
    timer = setTimeout(() => {
      term.value = q
      debouncing.value = false
    }, 200)
  }

  onScopeDispose(clear)

  return {
    districts: computed(() => (term.value ? (data.value ?? []) : [])),
    isDistrictsSearching: computed(
      () => debouncing.value || (Boolean(term.value) && isFetching.value),
    ),
    isDistrictsError: computed(() => Boolean(term.value) && !isFetching.value && isError.value),
    searchDistricts: search,
    clearDistrictSearch: clear,
  }
}
