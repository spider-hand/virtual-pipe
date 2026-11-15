import { QueryClient } from '@tanstack/vue-query'

export const createQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        networkMode: 'always',
        retry: false,
        refetchOnWindowFocus: false,
        refetchOnReconnect: false,
      },
      mutations: {
        networkMode: 'always',
        retry: false,
      },
    },
  })
