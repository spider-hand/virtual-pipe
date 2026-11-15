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

:slotted(.text-input) {
  box-sizing: border-box;
  width: 100%;
  min-width: 0;
  min-height: 44px;
  padding: var(--space-xs);
  border: 1px solid var(--color-muted);
  border-radius: var(--radius-md);
  background: var(--color-canvas);
  color: var(--color-ink);
  font: var(--font-body-md);
}

:slotted(.text-input::placeholder) {
  color: var(--color-muted);
  opacity: 1;
}

:slotted(.text-input:focus-visible) {
  outline: 2px solid var(--color-ink);
  outline-offset: 1px;
}
</style>
