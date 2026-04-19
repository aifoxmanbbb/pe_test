import { onBeforeUnmount, onMounted, watch } from 'vue'
import { setCssVar } from '@/utils'

type HeaderTheme = {
  bg: string
  text: string
  hover: string
}

const headerThemeDefaults: HeaderTheme = {
  bg: '',
  text: '',
  hover: ''
}

export const useHeaderTheme = (
  currentThemeKey: () => string,
  themeMap: Record<string, HeaderTheme>,
  fallbackKey: string
) => {
  const applyTheme = (key: string) => {
    const theme = themeMap[key] || themeMap[fallbackKey]
    if (!theme) return
    setCssVar('--top-header-bg-color', theme.bg)
    setCssVar('--top-header-text-color', theme.text)
    setCssVar('--top-header-hover-color', theme.hover)
  }

  const restoreTheme = () => {
    setCssVar('--top-header-bg-color', headerThemeDefaults.bg)
    setCssVar('--top-header-text-color', headerThemeDefaults.text)
    setCssVar('--top-header-hover-color', headerThemeDefaults.hover)
  }

  onMounted(() => {
    const rootStyle = getComputedStyle(document.documentElement)
    headerThemeDefaults.bg = rootStyle.getPropertyValue('--top-header-bg-color').trim()
    headerThemeDefaults.text = rootStyle.getPropertyValue('--top-header-text-color').trim()
    headerThemeDefaults.hover = rootStyle.getPropertyValue('--top-header-hover-color').trim()
    applyTheme(currentThemeKey())
  })

  watch(currentThemeKey, (key) => {
    applyTheme(key)
  })

  onBeforeUnmount(() => {
    restoreTheme()
  })
}
