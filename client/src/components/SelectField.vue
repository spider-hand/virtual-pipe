<script setup lang="ts" generic="Value extends string">
import { ChevronDown } from '@lucide/vue'

defineOptions({ inheritAttrs: false })
defineProps<{ options: readonly { value: Value; label: string; disabled?: boolean }[] }>()

const value = defineModel<Value>({ required: true })
</script>

<template>
  <span class="select-field">
    <select v-model="value" v-bind="$attrs">
      <option
        v-for="option in options"
        :key="option.value"
        :value="option.value"
        :disabled="option.disabled"
      >
        {{ option.label }}
      </option>
    </select>
    <ChevronDown aria-hidden="true" :size="16" />
  </span>
</template>

<style scoped>
.select-field {
  position: relative;
  display: block;
  min-width: 0;
}

select {
  box-sizing: border-box;
  width: 100%;
  min-width: 0;
  min-height: 44px;
  padding: var(--space-xs);
  padding-inline-end: calc(var(--space-lg) + 16px);
  appearance: none;
  border: 1px solid var(--color-muted);
  border-radius: var(--radius-md);
  background: var(--color-canvas);
  color: var(--color-ink);
  font: var(--font-body-md);
}

select:disabled {
  color: var(--color-muted);
}

select:focus-visible {
  outline: 2px solid var(--color-ink);
  outline-offset: 1px;
}

svg {
  position: absolute;
  inset-block-start: 50%;
  inset-inline-end: var(--space-sm);
  transform: translateY(-50%);
  pointer-events: none;
}
</style>
