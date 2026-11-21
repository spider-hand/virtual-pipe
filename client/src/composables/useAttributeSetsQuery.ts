import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'
import { computed, type Ref } from 'vue'

import { AttributeSetsApi, Configuration, type AttributeSetCreate } from '@/services'

const api = new AttributeSetsApi(new Configuration({ basePath: '' }))

const attributeSetsKey = ['attributeSets'] as const

export const useAttributeSetsQuery = (active: Readonly<Ref<boolean>> | boolean = false) => {
  const client = useQueryClient()

  const { data, isFetching, isError } = useQuery({
    queryKey: attributeSetsKey,
    queryFn: ({ signal }) => api.listAttributeSets({ signal }),
    enabled: active,
  })

  const {
    data: savedSet,
    isError: createFailed,
    isPending,
    mutateAsync,
    reset,
  } = useMutation({
    mutationFn: (attributeSetCreate: AttributeSetCreate) =>
      api.createAttributeSet({ attributeSetCreate }),
    onSuccess: () => {
      void client.invalidateQueries({ queryKey: attributeSetsKey })
    },
  })

  const create = async (attributeSetCreate: AttributeSetCreate) => {
    await mutateAsync(attributeSetCreate).catch(() => undefined)
  }

  const clearSaved = () => {
    if (savedSet.value) reset()
  }

  return {
    attributeSets: computed(() => data.value ?? []),
    isAttributeSetsFetching: isFetching,
    isAttributeSetsError: isError,
    createAttributeSet: create,
    attributeSet: computed(() => savedSet.value ?? null),
    isAttributeSetPending: isPending,
    isAttributeSetError: createFailed,
    resetAttributeSet: clearSaved,
  }
}
