import { createRouter, createWebHistory } from 'vue-router'

import MapPage from '@/pages/MapPage.vue'
import RoadDataSetupPage from '@/pages/RoadDataSetupPage.vue'

export const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', name: 'map', component: MapPage },
    { path: '/setup', name: 'setup', component: RoadDataSetupPage },
  ],
})
