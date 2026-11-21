<script setup lang="ts">
import AreaSearch from '@/components/AreaSearch.vue'
import { useDistrictsQuery } from '@/composables/useDistrictsQuery'
import type { District } from '@/services'

defineProps<{ disabled?: boolean; selectionRequired?: boolean }>()
const emit = defineEmits<{ select: [district: District]; clearSelection: [] }>()
const { districts, isDistrictsSearching, isDistrictsError, searchDistricts, clearDistrictSearch } =
  useDistrictsQuery()
</script>

<template>
  <AreaSearch
    mode="district"
    :results="districts"
    :loading="isDistrictsSearching"
    :unavailable="isDistrictsError"
    :disabled="disabled"
    :selection-required="selectionRequired"
    @search="searchDistricts"
    @clear-search="clearDistrictSearch"
    @select="emit('select', $event)"
    @clear-selection="emit('clearSelection')"
  />
</template>
