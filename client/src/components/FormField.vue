<script setup lang="ts">
defineProps<{ label: string }>()
</script>

<template>
  <label class="field">
    {{ label }}
    <slot />
  </label>
</template>

<style scoped>
.field {
  display: grid;
  min-width: 0;
  gap: var(--space-xxs);
  font: var(--font-body-sm);
}
</style>
