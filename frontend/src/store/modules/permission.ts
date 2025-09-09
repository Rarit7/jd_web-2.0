import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { RouteRecordRaw } from 'vue-router'

export const usePermissionStore = defineStore('permission', () => {
  const routes = ref<RouteRecordRaw[]>([])
  const addRoutes = ref<RouteRecordRaw[]>([])

  const setRoutes = (newRoutes: RouteRecordRaw[]) => {
    addRoutes.value = newRoutes
    routes.value = newRoutes
  }

  return {
    routes,
    addRoutes,
    setRoutes
  }
})