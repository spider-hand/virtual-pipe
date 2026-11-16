import { createRouter, createWebHistory } from 'vue-router'

import Map from '@/components/Map.vue'
import RoadDataSetup from '@/components/RoadDataSetup.vue'

export const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', name: 'map', component: Map },
    { path: '/setup', name: 'setup', component: RoadDataSetup },
  ],
})
