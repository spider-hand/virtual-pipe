<script setup lang="ts">
import AppMap from '@/components/AppMap.vue'
import AppSidebar from '@/components/AppSidebar.vue'
</script>

<template>
  <div class="app-layout">
    <AppSidebar />
    <main class="map-area">
      <AppMap />
    </main>
  </div>
</template>

<style>
body {
  margin: 0;
}
</style>

<style scoped>
.app-layout {
  display: flex;
  height: 100dvh;
}

.map-area {
  flex: 1;
  min-width: 0;
}
</style>
