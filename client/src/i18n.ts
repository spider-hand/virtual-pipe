import { createI18n } from 'vue-i18n'

import en from '@/locales/en.json'
import ja from '@/locales/ja.json'

export const createAppI18n = (language = navigator.language) =>
  createI18n({
    legacy: false,
    locale: language.toLowerCase().startsWith('ja') ? 'ja' : 'en',
    fallbackLocale: 'en',
    messages: { en, ja },
  })
