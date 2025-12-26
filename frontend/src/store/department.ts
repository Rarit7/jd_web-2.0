import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Department, TgAccountInfo } from '@/api/department'
import {
  getDepartmentList,
  createDepartment,
  updateDepartment,
  deleteDepartment,
  getAvailableTgAccounts
} from '@/api/department'

export const useDepartmentStore = defineStore('department', () => {
  const departments = ref<Department[]>([])
  const currentDepartment = ref<Department | null>(null)
  const availableTgAccounts = ref<TgAccountInfo[]>([])
  const loading = ref(false)

  // 获取部门列表
  async function fetchDepartments() {
    loading.value = true
    try {
      const res = await getDepartmentList()
      if (res.err_code === 0) {
        departments.value = res.payload.data
      }
      return res
    } finally {
      loading.value = false
    }
  }

  // 创建部门
  async function addDepartment(data: { name: string; description?: string }) {
    const res = await createDepartment(data)
    if (res.err_code === 0) {
      await fetchDepartments()
    }
    return res
  }

  // 更新部门
  async function modifyDepartment(id: number, data: { name?: string; description?: string; is_active?: number }) {
    const res = await updateDepartment(id, data)
    if (res.err_code === 0) {
      await fetchDepartments()
    }
    return res
  }

  // 删除部门
  async function removeDepartment(id: number) {
    const res = await deleteDepartment(id)
    if (res.err_code === 0) {
      await fetchDepartments()
    }
    return res
  }

  // 获取可用的TG账户列表
  async function fetchAvailableTgAccounts() {
    const res = await getAvailableTgAccounts()
    if (res.err_code === 0) {
      availableTgAccounts.value = res.payload.data
    }
    return res
  }

  // 根据ID查找部门
  function getDepartmentById(id: number) {
    return departments.value.find(dept => dept.id === id)
  }

  // 重置状态
  function reset() {
    departments.value = []
    currentDepartment.value = null
    availableTgAccounts.value = []
  }

  return {
    departments,
    currentDepartment,
    availableTgAccounts,
    loading,
    fetchDepartments,
    addDepartment,
    modifyDepartment,
    removeDepartment,
    fetchAvailableTgAccounts,
    getDepartmentById,
    reset
  }
})
