import request from './request'
import type { ApiResponse } from '@/types/api'

// 安全用户信息接口
export interface SecureUser {
  id: number
  username: string
  role_name: string
  role_id: number  // 兼容旧系统
  permission_level: number
  permission_name: string
  status: number
  last_login: string
  created_at: string
}

// 权限等级接口
export interface PermissionLevel {
  id: number
  name: string
}

// 安全登录
export const secureLogin = async (username: string, password: string): Promise<ApiResponse<{ user: SecureUser }>> => {
  const response = await request.post('/user/secure_login', {
    username,
    password
  })
  return response.data
}

// 安全登出
export const secureLogout = async (): Promise<ApiResponse<{ message: string }>> => {
  const response = await request.post('/user/secure_logout')
  return response.data
}

// 获取当前安全用户信息
export const getSecureUserInfo = async (): Promise<ApiResponse<SecureUser>> => {
  const response = await request.get('/user/secure_info')
  return response.data
}

// 获取安全用户列表
export const getSecureUserList = async (): Promise<ApiResponse<{ users: SecureUser[]; roles: PermissionLevel[] }>> => {
  const response = await request.get('/user/secure/list')
  return response.data
}

// 创建安全用户
export const createSecureUser = async (userData: {
  username: string
  password?: string
  permission_level: number
}): Promise<ApiResponse<{ message: string; user_id: number; default_password: string }>> => {
  const response = await request.post('/user/secure/create', userData)
  return response.data
}

// 更新安全用户
export const updateSecureUser = async (userData: {
  user_id: number
  permission_level: number
  status?: number
}): Promise<ApiResponse<{ message: string }>> => {
  const response = await request.post('/user/secure/update', userData)
  return response.data
}

// 删除（禁用）安全用户
export const deleteSecureUser = async (userId: number): Promise<ApiResponse<{ message: string }>> => {
  const response = await request.post('/user/secure/delete', {
    user_id: userId
  })
  return response.data
}


// 重置用户密码
export const resetUserPassword = async (userId: number, newPassword?: string): Promise<ApiResponse<{ 
  message: string
  new_password: string 
}>> => {
  const response = await request.post('/user/secure/reset_password', {
    user_id: userId,
    new_password: newPassword
  })
  return response.data
}

// 修改密码
export const changePassword = async (oldPassword: string, newPassword: string, confirmPassword: string): Promise<ApiResponse<{ message: string }>> => {
  const response = await request.post('/user/change_password', {
    old_password: oldPassword,
    new_password: newPassword,
    confirm_password: confirmPassword
  })
  return response.data
}

// 获取用户详细信息
export const getSecureUserDetail = async (userId: number): Promise<ApiResponse<{ user: SecureUser }>> => {
  const response = await request.get('/user/secure/info', {
    params: { user_id: userId }
  })
  return response.data
}