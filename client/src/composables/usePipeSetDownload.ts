import { ref } from 'vue'

import { Configuration, PipesetsApi } from '@/services'

const api = new PipesetsApi(new Configuration({ basePath: '' }))

export const usePipeSetDownload = () => {
  const pending = ref(false)
  const failed = ref(false)

  const download = async (id: string, fileFormat: 'csv' | 'parquet') => {
    if (pending.value) return

    pending.value = true
    failed.value = false

    try {
      const file = await api.downloadPipeSet({ id, fileFormat })
      if (!file.name) throw new Error('Missing download filename')

      const url = URL.createObjectURL(file)
      const link = document.createElement('a')
      link.href = url
      link.download = file.name

      try {
        link.click()
      } finally {
        window.setTimeout(() => URL.revokeObjectURL(url), 0)
      }
    } catch {
      failed.value = true
    } finally {
      pending.value = false
    }
  }

  return {
    downloadPipeSet: download,
    isPipeSetDownloadPending: pending,
    isPipeSetDownloadError: failed,
  }
}
