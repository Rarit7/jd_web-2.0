// API响应格式
export interface ApiResponse<T = any> {
  err_code: number
  err_msg: string
  payload: T
}

// 用户信息
export interface UserInfo {
  id: number
  username: string
  role_ids: number[]
}

// 登录请求
export interface LoginRequest {
  username: string
  password: string
}

// 登录响应
export interface LoginResponse {
  user: UserInfo
  token?: string
}