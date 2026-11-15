import { ref, shallowRef } from 'vue'

import { AttributeSetsApi, Configuration, type AttributeSet } from '@/services'

const api = new AttributeSetsApi(new Configuration({ basePath: '' }))

export const useAttributeSetsQuery = () => {
  const sets = shallowRef<AttributeSet[]>([])
  const loading = ref(false)
  const failed = ref(false)

  const load = async () => {
    if (loading.value) return

    loading.value = true
    failed.value = false

    try {
      sets.value = await api.listAttributeSets()
    } catch {
      failed.value = true
    } finally {
      loading.value = false
    }
  }

  return { sets, loading, failed, load }
}
