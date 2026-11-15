<script setup lang="ts">
import AreaSearch from '@/components/AreaSearch.vue'
import { useDistrictsQuery } from '@/composables/useDistrictsQuery'
import type { District } from '@/services'

defineProps<{ disabled?: boolean; selectionRequired?: boolean }>()
const emit = defineEmits<{ select: [district: District]; clearSelection: [] }>()
const { results, loading, unavailable, search, clear } = useDistrictsQuery()
</script>

<template>
  <AreaSearch
    mode="district"
    :results="results"
    :loading="loading"
    :unavailable="unavailable"
    :disabled="disabled"
    :selection-required="selectionRequired"
    @search="search"
    @clear-search="clear"
    @select="emit('select', $event)"
    @clear-selection="emit('clearSelection')"
  />
</template>
