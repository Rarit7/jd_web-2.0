import request from './request'

export interface BlackKeyword {
  id: number
  keyword: string
  status: number  // 0: 启用, 1: 禁用
  is_delete: number  // 0: 正常, 1: 已删除
  created_at: string
  updated_at: string
}

export interface BlackKeywordListParams {
  page: number
  page_size: number
  keyword?: string
}

export interface BlackKeywordCreateParams {
  keyword: string
  status: number
}

export interface BlackKeywordUpdateParams {
  keyword: string
  status: number
}

// API响应类型
export interface ApiResponse<T = any> {
  err_code: number
  err_msg: string
  payload: T
}

export interface PaginationResponse<T> {
  data: T[]
  total: number
  page: number
  page_size: number
}

export const blackWordsApi = {
  // 获取黑词列表
  getList(params: BlackKeywordListParams) {
    return request.get<ApiResponse<PaginationResponse<BlackKeyword>>>('/black-keywords', {
      params
    })
  },

  // 创建黑词
  create(data: BlackKeywordCreateParams) {
    return request.post<ApiResponse<BlackKeyword>>('/black-keywords', data)
  },

  // 更新黑词
  update(id: number, data: BlackKeywordUpdateParams) {
    return request.put<ApiResponse<BlackKeyword>>(`/black-keywords/${id}`, data)
  },

  // 删除黑词
  delete(id: number) {
    return request.delete<ApiResponse<null>>(`/black-keywords/${id}`)
  }
}