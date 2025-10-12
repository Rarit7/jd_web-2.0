import request from './request'
import type { ApiResponse } from '@/types/api'

// Telegram账户接口
export interface TgAccount {
  id: number
  name: string
  phone: string
  user_id: string
  username: string
  nickname: string
  status: number
  status_text: string
  two_step: number
  creator_id: number
  creator_username: string
  created_at: string
  updated_at: string
}

// Telegram账户绑定响应接口
export interface TgBindResponse {
  message: string
  user_id: number
  success?: boolean
  error?: string
}

// 账户状态响应接口
export interface TgAccountStatusResponse {
  id: number
  phone: string
  status: number
  status_text: string
  two_step: number
  user_id: string
  username: string
  nickname: string
}

// 账户群组响应接口
export interface TgAccountGroup {
  id: number
  chat_id: string
  title: string
  type: string
  status: string
  session_name: string
  created_at: string
}

// 添加账户参数接口
export interface AddAccountParams {
  name: string
  phone: string
}

// 发送验证码参数接口
export interface SendCodeParams {
  phone: string
}

// 验证码验证参数接口
export interface VerifyCodeParams {
  phone: string
  code: string
}


// 更新密码参数接口
export interface UpdatePasswordParams {
  phone: string
  password: string
}


// 获取Telegram账户列表
export const getTgAccountList = async (): Promise<ApiResponse<TgAccount[]>> => {
  const response = await request.get('/tg/account/list')
  return response.data
}

// 添加Telegram账户
export const addTgAccount = async (params: AddAccountParams): Promise<ApiResponse<any>> => {
  const response = await request.post('/tg/account/add', params)
  return response.data
}

// 发送手机验证码
export const sendPhoneCode = async (params: SendCodeParams): Promise<ApiResponse<any>> => {
  const response = await request.post('/tg/account/send_code', params)
  return response.data
}

// 验证验证码
export const verifyCode = async (params: VerifyCodeParams): Promise<ApiResponse<any>> => {
  const response = await request.post('/tg/account/verify', params)
  return response.data
}

// 检查是否需要2FA验证
export const checkTwoStepVerification = async (phone: string): Promise<ApiResponse<{ two_step: number }>> => {
  const response = await request.get(`/tg/account/tow_step_check?phone=${phone}`)
  return response.data
}


// 更新2FA密码
export const updatePassword = async (params: UpdatePasswordParams): Promise<ApiResponse<any>> => {
  const response = await request.post('/tg/account/update_password', params)
  return response.data
}


// 获取账户状态
export const getAccountStatus = async (accountId: number): Promise<ApiResponse<TgAccountStatusResponse>> => {
  const response = await request.get(`/tg/account/status/${accountId}`)
  return response.data
}

// 通过手机号检查状态（用于轮询）
export const checkAccountStatusByPhone = async (phone: string): Promise<ApiResponse<TgAccountStatusResponse & { is_processing: boolean }>> => {
  const response = await request.get(`/tg/account/check_status/${phone}`)
  return response.data
}

// 删除账户
export const deleteAccount = async (accountId: number): Promise<ApiResponse<any>> => {
  const response = await request.get(`/tg/account/delete?id=${accountId}`)
  return response.data
}

// 搜索聊天记录
export const searchChatHistory = async (accountIds: string): Promise<ApiResponse<any>> => {
  const response = await request.post('/tg/account/chat/search', {
    account_id: accountIds
  })
  return response.data
}

// 搜索群组
export const searchGroups = async (accountIds: string): Promise<ApiResponse<any>> => {
  const response = await request.post('/tg/account/group/search', {
    account_id: accountIds
  })
  return response.data
}

// 绑定Telegram账户（需要登录）
export const bindTelegramAccount = async (): Promise<ApiResponse<TgBindResponse>> => {
  const response = await request.post('/tg/account/bind')
  return response.data
}

// 测试绑定Telegram账户（无需登录）
export const bindTelegramAccountTest = async (userId?: string | number): Promise<ApiResponse<TgBindResponse>> => {
  const response = await request.post('/tg/account/bind_test', {
    user_id: userId || 'test_user'
  })
  return response.data
}

// 获取账户群组信息并建立会话关系
export const fetchAccountGroupInfo = async (accountId: number): Promise<ApiResponse<any>> => {
  const response = await request.post('/tg/account/fetch_group_info', {
    account_id: accountId
  })
  return response.data
}

// 批量获取多个账户的群组信息
export const fetchAccountGroupInfoBatch = async (accountIds: string): Promise<ApiResponse<any>> => {
  const response = await request.post('/tg/account/fetch_group_info_batch', {
    account_ids: accountIds
  })
  return response.data
}

// 获取账户的关联群组列表
export const getAccountGroups = async (accountId: number): Promise<ApiResponse<TgAccountGroup[]>> => {
  const response = await request.get(`/tg/account/${accountId}/groups`)
  return response.data
}

// 获取账户的私人聊天历史记录
export const fetchPersonChatHistory = async (accountId: number): Promise<ApiResponse<any>> => {
  const response = await request.post('/tg/account/fetch_person_chat', {
    account_id: String(accountId)
  })
  return response.data
}