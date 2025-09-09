import request from './request'
import type { LoginRequest, LoginResponse } from '@/types/api'

export const authApi = {
  // 用户登录
  login(data: LoginRequest) {
    return request.post<LoginResponse>('/user/login', data)
  },

  // 用户登出
  logout() {
    return request.post('/user/logout')
  },

  // 获取用户信息
  getUserInfo() {
    return request.get('/user/info')
  }
}