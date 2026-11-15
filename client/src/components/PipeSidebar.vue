<script setup lang="ts">
import { PanelLeftClose, PanelLeftOpen } from '@lucide/vue'
import { nextTick, ref, useId, useTemplateRef } from 'vue'
import { useI18n } from 'vue-i18n'

import AttributeSetEditor from '@/components/AttributeSetEditor.vue'
import PipeSetGenerator from '@/components/PipeSetGenerator.vue'
import type { District, Prefecture } from '@/services'

const { t } = useI18n({ useScope: 'global' })
const open = defineModel<boolean>('open', { required: true })
const emit = defineEmits<{
  areaChange: [area: District | Prefecture | null]
  pipesetReady: [id: string]
}>()
const tabs = ['attributes', 'generate'] as const
const activeTab = ref<(typeof tabs)[number]>('attributes')
const id = useId()
const launcher = useTemplateRef<HTMLButtonElement>('launcher')
const tablist = useTemplateRef<HTMLDivElement>('tablist')

const focusTab = () => {
  tablist.value?.querySelector<HTMLButtonElement>('[aria-selected=true]')?.focus()
}

const toggle = async () => {
  open.value = !open.value
  await nextTick()

  if (open.value) focusTab()
  else launcher.value?.focus()
}

const moveTab = async (event: KeyboardEvent) => {
  switch (event.key) {
    case 'Home':
      activeTab.value = 'attributes'
      break
    case 'End':
      activeTab.value = 'generate'
      break
    case 'ArrowLeft':
    case 'ArrowRight':
      activeTab.value = activeTab.value === 'attributes' ? 'generate' : 'attributes'
      break
    default:
      return
  }

  event.preventDefault()
  await nextTick()
  focusTab()
}
</script>

<template>
  <div class="sidebar-overlay">
    <button
      v-show="!open"
      ref="launcher"
      class="icon-button launcher"
      type="button"
      :aria-label="t('components.PipeSidebar.open')"
      :aria-controls="id"
      :aria-expanded="open"
      @click="toggle"
    >
      <PanelLeftOpen aria-hidden="true" :size="20" />
    </button>

    <aside v-show="open" :id="id" :aria-label="t('components.PipeSidebar.label')" class="sidebar">
      <header class="sidebar-header">
        <div
          ref="tablist"
          class="tabs"
          role="tablist"
          :aria-label="t('components.PipeSidebar.label')"
          @keydown="moveTab"
        >
          <button
            v-for="tab in tabs"
            :id="`${id}-tab-${tab}`"
            :key="tab"
            type="button"
            role="tab"
            :aria-controls="`${id}-panel-${tab}`"
            :aria-selected="activeTab === tab"
            :tabindex="activeTab === tab ? 0 : -1"
            @click="activeTab = tab"
          >
            {{ t(`components.PipeSidebar.${tab}`) }}
          </button>
        </div>
        <button
          class="icon-button close"
          type="button"
          :aria-label="t('components.PipeSidebar.close')"
          @click="toggle"
        >
          <PanelLeftClose aria-hidden="true" :size="20" />
        </button>
      </header>

      <div
        v-show="activeTab === 'attributes'"
        :id="`${id}-panel-attributes`"
        :aria-labelledby="`${id}-tab-attributes`"
        class="attribute-panel"
        role="tabpanel"
      >
        <AttributeSetEditor />
      </div>

      <div
        v-show="activeTab === 'generate'"
        :id="`${id}-panel-generate`"
        :aria-labelledby="`${id}-tab-generate`"
        class="generate-panel"
        role="tabpanel"
      >
        <PipeSetGenerator
          :active="open && activeTab === 'generate'"
          @area-change="emit('areaChange', $event)"
          @pipeset-ready="emit('pipesetReady', $event)"
        />
      </div>
    </aside>
  </div>
</template>

<style scoped>
.sidebar-overlay {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  max-height: 100%;
}

.sidebar {
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  align-self: stretch;
  width: 100%;
  overflow: hidden;
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-lg);
  background: var(--color-canvas);
  color: var(--color-ink);
  pointer-events: auto;
}

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-xxs);
  padding: var(--space-xs);
  border-bottom: 1px solid var(--color-hairline);
}

.tabs {
  display: flex;
  min-width: 0;
  gap: var(--space-xxs);
}

button {
  min-height: 44px;
  border: 0;
  background: transparent;
  color: inherit;
  cursor: pointer;
  font: var(--font-button);
}

.tabs button {
  padding: var(--space-xs);
  border-radius: var(--radius-pill);
  color: var(--color-muted);
  line-height: 1.2;
}

.tabs [aria-selected='true'] {
  background: var(--color-surface-card);
  color: var(--color-ink);
}

.icon-button {
  display: grid;
  flex: none;
  width: 44px;
  place-items: center;
  border-radius: var(--radius-md);
}

.launcher {
  border: 1px solid var(--color-hairline);
  background: var(--color-canvas);
  pointer-events: auto;
}

button:hover {
  background: var(--color-surface-strong);
}

button:focus-visible {
  outline: 2px solid var(--color-ink);
  outline-offset: -2px;
}

.attribute-panel {
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.generate-panel {
  min-height: 0;
  overflow: auto;
}
</style>
