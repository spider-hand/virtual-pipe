import { ref, shallowRef } from 'vue'

import {
  AttributeSetsApi,
  Configuration,
  type AttributeSet,
  type AttributeSetCreate,
} from '@/services'

const api = new AttributeSetsApi(new Configuration({ basePath: '' }))

export const useCreateAttributeSet = () => {
  const saved = shallowRef<AttributeSet | null>(null)
  const failed = ref(false)

  const create = async (attributeSetCreate: AttributeSetCreate) => {
    failed.value = false

    try {
      saved.value = await api.createAttributeSet({ attributeSetCreate })
    } catch {
      failed.value = true
    }
  }

  const clearSaved = () => {
    saved.value = null
  }

  return { create, saved, failed, clearSaved }
}
