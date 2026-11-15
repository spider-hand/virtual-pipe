import { VueQueryPlugin } from '@tanstack/vue-query'
import { createApp } from 'vue'

import App from '@/App.vue'
import { createAppI18n } from '@/i18n'
import { createQueryClient } from '@/queryClient'
import '@/styles/tokens.css'

const i18n = createAppI18n()
document.documentElement.lang = i18n.global.locale.value

createApp(App).use(i18n).use(VueQueryPlugin, { queryClient: createQueryClient() }).mount('#app')
