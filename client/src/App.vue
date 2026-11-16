<script setup lang="ts">
import { RouterView } from 'vue-router'
</script>

<template>
  <RouterView v-slot="{ Component }">
    <KeepAlive include="MapPage">
      <component :is="Component" />
    </KeepAlive>
  </RouterView>
</template>

<style>
body {
  margin: 0;
}
</style>
