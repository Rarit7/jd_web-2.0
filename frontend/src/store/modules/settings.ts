import { defineStore } from 'pinia'
import { ref } from 'vue'
import { DEFAULT_SETTINGS } from '@/constants'

export const useSettingsStore = defineStore('settings', () => {
  // 系统设置
  const title = ref(DEFAULT_SETTINGS.title)
  const fixedHeader = ref(DEFAULT_SETTINGS.fixedHeader)
  const showTagsView = ref(DEFAULT_SETTINGS.showTagsView)
  const showSidebarLogo = ref(DEFAULT_SETTINGS.showSidebarLogo)
  const showSettings = ref(DEFAULT_SETTINGS.showSettings)
  const showBreadcrumb = ref(DEFAULT_SETTINGS.showBreadcrumb)
  const showBreadcrumbIcon = ref(DEFAULT_SETTINGS.showBreadcrumbIcon)

  // 主题设置
  const primaryColor = ref('#409eff')

  // 布局设置
  const sidebarWidth = ref(DEFAULT_SETTINGS.sidebarWidth)
  const sidebarCollapsedWidth = ref(DEFAULT_SETTINGS.sidebarCollapsedWidth)

  // 更新设置
  const updateSettings = (settings: Partial<typeof DEFAULT_SETTINGS>) => {
    Object.keys(settings).forEach(key => {
      const value = settings[key as keyof typeof settings]
      if (value !== undefined) {
        switch (key) {
          case 'title':
            title.value = value as string
            break
          case 'fixedHeader':
            fixedHeader.value = value as boolean
            break
          case 'showTagsView':
            showTagsView.value = value as boolean
            break
          case 'showSidebarLogo':
            showSidebarLogo.value = value as boolean
            break
          case 'showSettings':
            showSettings.value = value as boolean
            break
          case 'showBreadcrumb':
            showBreadcrumb.value = value as boolean
            break
          case 'showBreadcrumbIcon':
            showBreadcrumbIcon.value = value as boolean
            break
        }
      }
    })
  }


  return {
    title,
    fixedHeader,
    showTagsView,
    showSidebarLogo,
    showSettings,
    showBreadcrumb,
    showBreadcrumbIcon,
    primaryColor,
    sidebarWidth,
    sidebarCollapsedWidth,
    updateSettings
  }
})