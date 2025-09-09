import { defineStore } from 'pinia'
import { ref } from 'vue'
import { STORAGE_KEYS } from '@/constants'

export interface SidebarState {
  opened: boolean
  withoutAnimation: boolean
}

export const useAppStore = defineStore('app', () => {
  // 侧边栏状态
  const sidebar = ref<SidebarState>({
    opened: localStorage.getItem(STORAGE_KEYS.SIDEBAR_STATUS) ? 
      !!+localStorage.getItem(STORAGE_KEYS.SIDEBAR_STATUS)! : true,
    withoutAnimation: false
  })

  // 设备类型
  const device = ref<'desktop' | 'mobile'>('desktop')

  // 语言
  const language = ref(localStorage.getItem(STORAGE_KEYS.LANGUAGE) || 'zh-CN')

  // 切换侧边栏
  const toggleSidebar = () => {
    sidebar.value.opened = !sidebar.value.opened
    sidebar.value.withoutAnimation = false
    if (sidebar.value.opened) {
      localStorage.setItem(STORAGE_KEYS.SIDEBAR_STATUS, '1')
    } else {
      localStorage.setItem(STORAGE_KEYS.SIDEBAR_STATUS, '0')
    }
  }

  // 关闭侧边栏
  const closeSideBar = (withoutAnimation: boolean) => {
    localStorage.setItem(STORAGE_KEYS.SIDEBAR_STATUS, '0')
    sidebar.value.opened = false
    sidebar.value.withoutAnimation = withoutAnimation
  }

  // 切换设备类型
  const toggleDevice = (deviceType: 'desktop' | 'mobile') => {
    device.value = deviceType
  }

  // 设置语言
  const setLanguage = (lang: string) => {
    language.value = lang
    localStorage.setItem(STORAGE_KEYS.LANGUAGE, lang)
  }

  return {
    sidebar,
    device,
    language,
    toggleSidebar,
    closeSideBar,
    toggleDevice,
    setLanguage
  }
})