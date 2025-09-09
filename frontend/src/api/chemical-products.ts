import request from './request'

export interface ChemicalProduct {
  id: number
  platform_id: number
  platform_name: string
  product_name: string
  seller_name: string
  compound_name: string
  contact_number: string
  qq_number: string
  status: number  // 0-待处理 1-处理中 2-已处理
  created_at: string
  updated_at: string
}

export interface ChemicalPlatform {
  id: number
  name: string
}

export interface ChemicalProductListParams {
  page: number
  page_size: number
  search_product_name?: string
  search_compound_name?: string
  search_contact_number?: string
  search_qq_number?: string
  search_platform_id?: number[]
}

// API响应类型
export interface ApiResponse<T = any> {
  err_code: number
  err_msg: string
  payload: T
}

export interface PaginationResponse<T> {
  data: T[]
  total_records: number
  total_pages: number
  current_page: number
  page_size: number
  platform_list: ChemicalPlatform[]
}

export const chemicalProductsApi = {
  // 获取化工产品列表
  getList(params: ChemicalProductListParams) {
    return request.get<ApiResponse<PaginationResponse<ChemicalProduct>>>('/chemical-products', {
      params
    })
  },

  // 删除化工产品
  delete(id: number) {
    return request.delete<ApiResponse<null>>(`/chemical-products/${id}`)
  },

  // 下载化工产品数据
  download(params: Partial<ChemicalProductListParams>) {
    return request.get('/chemical-products/download', {
      params,
      responseType: 'blob'
    })
  },

  // 启动化工产品搜索/爬取
  startSearch(platformId: number) {
    return request.post<ApiResponse<null>>('/chemical-products/search', {
      platform_id: platformId
    })
  }
}