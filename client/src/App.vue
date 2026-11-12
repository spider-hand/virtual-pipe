<script setup lang="ts">
import { onMounted } from 'vue'

import { useHealthQuery } from '@/composables/useHealthQuery'

defineOptions({ render: () => null })

const { checkHealth } = useHealthQuery()

onMounted(checkHealth)
</script>
