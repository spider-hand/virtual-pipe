import { VueQueryPlugin } from '@tanstack/vue-query'
import type { Plugin } from 'vue'

import { createAppI18n } from '@/i18n'
import { createQueryClient } from '@/queryClient'

export const createTestPlugins = (queryClient = createQueryClient()): Plugin[] => [
  createAppI18n('en'),
  (app) => {
    app.use(VueQueryPlugin, { queryClient })
  },
]
