import request from './request'
import type { ApiResponse } from '@/types/api'

// 部门信息接口
export interface Department {
  id: number
  name: string
  description: string
  is_active: number
  user_count: number
  tg_account_count: number
  created_at: string
  updated_at: string
}

// TG账户信息接口
export interface TgAccountInfo {
  user_id: string
  phone: string
  username: string
  first_name: string
  last_name: string
  display_name: string
}

// 部门-TG账户关联接口
export interface DepartmentTgAccount {
  id: number
  department_id: number
  tg_user_id: string
  created_at: string
  created_by: number
  tg_account_info?: {
    id: number
    phone: string
    username: string
    user_id: string
  }
}

// 获取部门列表
export const getDepartmentList = async (): Promise<ApiResponse<{
  data: Department[]
  total: number
}>> => {
  const response = await request.get('/department/list')
  return response.data
}

// 创建部门
export const createDepartment = async (departmentData: {
  name: string
  description?: string
}): Promise<ApiResponse<{ data: Department }>> => {
  const response = await request.post('/department/create', departmentData)
  return response.data
}

// 更新部门
export const updateDepartment = async (deptId: number, departmentData: {
  name?: string
  description?: string
  is_active?: number
}): Promise<ApiResponse<{ data: Department }>> => {
  const response = await request.post(`/department/${deptId}/update`, departmentData)
  return response.data
}

// 删除部门
export const deleteDepartment = async (deptId: number): Promise<ApiResponse<{ message: string }>> => {
  const response = await request.post(`/department/${deptId}/delete`)
  return response.data
}

// 获取部门关联的TG账户列表
export const getDepartmentTgAccounts = async (deptId: number): Promise<ApiResponse<{
  data: DepartmentTgAccount[]
  department: Department
}>> => {
  const response = await request.get(`/department/${deptId}/tg_accounts`)
  return response.data
}

// 配置部门-TG账户关联（替换模式）
export const updateDepartmentTgAccounts = async (deptId: number, tgUserIds: string[]): Promise<ApiResponse<{
  message: string
  count: number
}>> => {
  const response = await request.post(`/department/${deptId}/tg_accounts`, {
    tg_user_ids: tgUserIds
  })
  return response.data
}

// 获取所有可用的TG账户列表（用于关联配置）
export const getAvailableTgAccounts = async (): Promise<ApiResponse<{
  data: TgAccountInfo[]
  total: number
}>> => {
  const response = await request.get('/tg_accounts/available')
  return response.data
}

// 添加单个TG账户关联
export const addDepartmentTgAccount = async (deptId: number, tgUserId: string): Promise<ApiResponse<{
  message: string
  data: DepartmentTgAccount
}>> => {
  const response = await request.post(`/department/${deptId}/tg_accounts/add`, {
    tg_user_id: tgUserId
  })
  return response.data
}

// 移除单个TG账户关联
export const removeDepartmentTgAccount = async (deptId: number, tgUserId: string): Promise<ApiResponse<{
  message: string
}>> => {
  const response = await request.post(`/department/${deptId}/tg_accounts/remove`, {
    tg_user_id: tgUserId
  })
  return response.data
}
