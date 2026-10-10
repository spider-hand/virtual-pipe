import { ref } from 'vue'
import { useDrawing } from '@/composables/useDrawing'

export const usePipeset = () => {
  const name = ref('')
  const count = ref<number | ''>(1)
  const { bbox } = useDrawing()

  return { name, count, bbox }
}
