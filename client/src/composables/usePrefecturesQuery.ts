import { useQuery } from '@tanstack/vue-query'
import { computed, type Ref } from 'vue'

import { Configuration, PrefecturesApi } from '@/services'

const api = new PrefecturesApi(new Configuration({ basePath: '' }))

export const usePrefecturesQuery = (active: Readonly<Ref<boolean>>) => {
  const { data, isFetching, isError } = useQuery({
    queryKey: ['prefectures'],
    queryFn: ({ signal }) => api.listPrefectures({ signal }),
    enabled: active,
    staleTime: Infinity,
  })

  return {
    prefectures: computed(() => data.value ?? []),
    loading: isFetching,
    unavailable: isError,
  }
}
