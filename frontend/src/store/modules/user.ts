import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { UserInfo } from '@/types/api'
import { STORAGE_KEYS } from '@/constants'

export const useUserStore = defineStore('user', () => {
  const userInfo = ref<UserInfo | null>(null)
  const token = ref<string>('')  // 保留以兼容现有代码，但session认证不使用
  const avatar = ref<string>('')

  const isLoggedIn = computed(() => !!userInfo.value)
  const roleIds = computed(() => userInfo.value?.role_ids || [])
  const isAdmin = computed(() => roleIds.value.includes(1))

  function setUser(user: UserInfo, authToken?: string) {
    userInfo.value = user
    // 对于session认证，我们仍然存储用户信息到localStorage以便页面刷新后恢复
    localStorage.setItem(STORAGE_KEYS.USER_INFO, JSON.stringify(user))
    if (authToken) {
      token.value = authToken
      localStorage.setItem(STORAGE_KEYS.TOKEN, authToken)
    }
  }

  function setAvatar(avatarUrl: string) {
    avatar.value = avatarUrl
  }

  function logout() {
    userInfo.value = null
    token.value = ''
    avatar.value = ''
    localStorage.removeItem(STORAGE_KEYS.TOKEN)
    localStorage.removeItem(STORAGE_KEYS.USER_INFO)
  }

  function initFromStorage() {
    const storedToken = localStorage.getItem(STORAGE_KEYS.TOKEN)
    const storedUser = localStorage.getItem(STORAGE_KEYS.USER_INFO)
    
    // 保留token逻辑以兼容可能的token认证
    if (storedToken) {
      token.value = storedToken
    }
    
    // 优先从localStorage恢复用户信息
    if (storedUser) {
      try {
        userInfo.value = JSON.parse(storedUser)
      } catch (e) {
        console.error('Failed to parse stored user info:', e)
        localStorage.removeItem(STORAGE_KEYS.USER_INFO)
      }
    }
  }

  return {
    userInfo,
    token,
    avatar,
    isLoggedIn,
    roleIds,
    isAdmin,
    setUser,
    setAvatar,
    logout,
    initFromStorage
  }
})