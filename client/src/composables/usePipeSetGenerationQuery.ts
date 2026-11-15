import { computed, onScopeDispose, ref } from 'vue'

import { Configuration, PipesetsApi, ResponseError, type PipeSetCreate } from '@/services'

const api = new PipesetsApi(new Configuration({ basePath: '' }))
const pollInterval = 10_000

export const usePipeSetGenerationQuery = ({
  onSucceeded,
}: {
  onSucceeded: (id: string) => void
}) => {
  const status = ref<
    | 'idle'
    | 'submitting'
    | 'submitFailed'
    | 'pending'
    | 'statusUnavailable'
    | 'notFound'
    | 'succeeded'
    | 'failed'
  >('idle')
  const busy = computed(
    () =>
      status.value === 'submitting' ||
      status.value === 'pending' ||
      status.value === 'statusUnavailable',
  )
  const controller = new AbortController()
  const { signal } = controller
  let timer: ReturnType<typeof setTimeout> | undefined

  const schedulePoll = (id: string) => {
    timer = setTimeout(() => void poll(id), pollInterval)
  }

  const poll = async (id: string) => {
    try {
      const result = await api.getPipeSetStatus({ id }, { signal })
      if (signal.aborted) return

      status.value = result.status
    } catch (error) {
      if (signal.aborted) return

      status.value =
        error instanceof ResponseError && error.response.status === 404
          ? 'notFound'
          : 'statusUnavailable'
    }

    if (status.value === 'succeeded') onSucceeded(id)
    if (busy.value) schedulePoll(id)
  }

  const submit = async (pipeSetCreate: PipeSetCreate) => {
    if (busy.value || signal.aborted) return

    status.value = 'submitting'

    try {
      const { id } = await api.createPipeSet({ pipeSetCreate }, { signal })
      if (signal.aborted) return

      status.value = 'pending'
      schedulePoll(id)
    } catch {
      if (!signal.aborted) status.value = 'submitFailed'
    }
  }

  onScopeDispose(() => {
    clearTimeout(timer)
    controller.abort()
  })

  return { status, busy, submit }
}
