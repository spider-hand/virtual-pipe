import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'
import { computed } from 'vue'

import {
  Configuration,
  ResponseError,
  RoadDataApi,
  type RoadData,
  type RoadDataRegionEnum,
} from '@/services'

const api = new RoadDataApi(new Configuration({ basePath: '' }))
const queryKey = ['road-data'] as const
const isActive = (setup: RoadData['setup'] | undefined) =>
  setup?.status === 'queued' || setup?.status === 'downloading' || setup?.status === 'importing'

export const useRoadDataQuery = () => {
  const client = useQueryClient()
  const { data, isError } = useQuery({
    queryKey,
    queryFn: ({ signal }) => api.getRoadData({ signal, cache: 'no-store' }),
    refetchInterval: ({ state }) => (isActive(state.data?.setup) ? 2_000 : false),
  })

  const {
    mutate: submit,
    isPending: submitting,
    error,
    variables: submittedRegion,
  } = useMutation({
    mutationFn: (region: RoadDataRegionEnum) =>
      api.createRoadDataSetup({ roadDataSetupRequest: { region } }),
    onSuccess: async (setup) => {
      await client.cancelQueries({ queryKey })
      client.setQueryData<RoadData>(queryKey, (current) => current && { ...current, setup })
    },
    onError: () => {
      void client.invalidateQueries({ queryKey })
    },
  })

  const submitError = computed(() => {
    if (error.value instanceof ResponseError && error.value.response.status === 409) {
      return data.value?.activeRegion === submittedRegion.value ? undefined : 'alreadyActive'
    }

    return error.value ? 'submitFailed' : undefined
  })

  return {
    roadData: data,
    isRoadDataError: isError,
    createRoadDataSetup: submit,
    isRoadDataSetupPending: submitting,
    roadDataSetupError: submitError,
    isRoadDataSetupActive: computed(() => isActive(data.value?.setup)),
  }
}
