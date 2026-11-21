import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'
import { computed, onScopeDispose, ref, watch } from 'vue'

import { Configuration, PipesetsApi, ResponseError, type PipeSetCreate } from '@/services'

const api = new PipesetsApi(new Configuration({ basePath: '' }))
const pipeSetsKey = ['pipeSets'] as const
const pipeSetsListKey = [...pipeSetsKey, 'list'] as const
const pipeSetStatusKey = (id: string) => [...pipeSetsKey, 'status', id] as const
const pollInterval = 10_000
const isNotFound = (error: unknown) =>
  error instanceof ResponseError && error.response.status === 404

export const usePipeSetsQuery = ({ onSucceeded }: { onSucceeded?: (id: string) => void } = {}) => {
  const client = useQueryClient()
  const { data, isFetching, isError, refetch } = useQuery({
    queryKey: pipeSetsListKey,
    queryFn: ({ signal }) => api.listPipeSets({ signal, cache: 'no-store' }),
    enabled: false,
  })

  const load = async () => {
    if (isFetching.value) void client.cancelQueries({ queryKey: pipeSetsListKey })
    const result = await refetch()
    if (result.isSuccess) return result.data
  }

  const id = ref('')
  const controller = new AbortController()

  const {
    mutateAsync,
    isPending,
    isError: submitFailed,
  } = useMutation({
    mutationFn: (pipeSetCreate: PipeSetCreate) =>
      api.createPipeSet({ pipeSetCreate }, { signal: controller.signal }),
    onSuccess: (accepted) => {
      if (controller.signal.aborted) return

      // The accepted job starts pending. Seeding it defers the first GET to the polling interval.
      client.setQueryData(pipeSetStatusKey(accepted.id), { id: accepted.id, status: 'pending' })
      id.value = accepted.id
    },
  })

  const { data: job, error } = useQuery({
    queryKey: computed(() => pipeSetStatusKey(id.value)),
    queryFn: ({ queryKey: [, , id], signal }) =>
      api.getPipeSetStatus({ id }, { signal, cache: 'no-store' }),
    enabled: computed(() => Boolean(id.value)),
    staleTime: Infinity,
    refetchInterval: ({ state }) =>
      state.data?.status === 'pending' && !isNotFound(state.error) ? pollInterval : false,
    refetchIntervalInBackground: true,
  })

  const status = computed(() => {
    if (isPending.value) return 'submitting'
    if (submitFailed.value) return 'submitFailed'
    if (!id.value) return 'idle'
    if (error.value) return isNotFound(error.value) ? 'notFound' : 'statusUnavailable'

    return job.value?.status ?? 'pending'
  })
  const busy = computed(
    () =>
      status.value === 'submitting' ||
      status.value === 'pending' ||
      status.value === 'statusUnavailable',
  )

  watch(status, (next) => {
    if (next === 'succeeded') onSucceeded?.(id.value)
  })

  const submit = async (pipeSetCreate: PipeSetCreate) => {
    if (busy.value || controller.signal.aborted) return

    id.value = ''
    await mutateAsync(pipeSetCreate).catch(() => undefined)
  }

  onScopeDispose(() => controller.abort())

  return {
    pipeSets: computed(() => data.value ?? []),
    isPipeSetsFetching: isFetching,
    isPipeSetsError: isError,
    loadPipeSets: load,
    pipeSetStatus: status,
    isPipeSetBusy: busy,
    createPipeSet: submit,
  }
}
