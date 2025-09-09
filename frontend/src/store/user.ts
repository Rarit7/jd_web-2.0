import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { UserInfo } from '@/types/api'

export const useUserStore = defineStore('user', () => {
  const userInfo = ref<UserInfo | null>(null)
  const token = ref<string>('')

  const isLoggedIn = computed(() => !!userInfo.value)
  const roleIds = computed(() => userInfo.value?.role_ids || [])
  const isAdmin = computed(() => roleIds.value.includes(1))

  function setUser(user: UserInfo, authToken?: string) {
    userInfo.value = user
    if (authToken) {
      token.value = authToken
      localStorage.setItem('token', authToken)
    }
    localStorage.setItem('userInfo', JSON.stringify(user))
  }

  function logout() {
    userInfo.value = null
    token.value = ''
    localStorage.removeItem('token')
    localStorage.removeItem('userInfo')
  }

  function initFromStorage() {
    const storedToken = localStorage.getItem('token')
    const storedUser = localStorage.getItem('userInfo')
    
    if (storedToken) {
      token.value = storedToken
    }
    
    if (storedUser) {
      try {
        userInfo.value = JSON.parse(storedUser)
      } catch (e) {
        console.error('Failed to parse stored user info:', e)
        localStorage.removeItem('userInfo')
      }
    }
  }

  return {
    userInfo,
    token,
    isLoggedIn,
    roleIds,
    isAdmin,
    setUser,
    logout,
    initFromStorage
  }
})