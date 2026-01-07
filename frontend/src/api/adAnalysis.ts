/**
 * 数据分析系统 (Ad Analysis) API 服务
 */
import axios from 'axios'
import type {
  AnalysisFilters,
  DarkKeywordsAnalysisResponse,
  DarkKeywordCategory,
  TransactionMethodsResponse,
  TransactionMethodsTrendResponse,
  PriceTrendResponse,
  PriceHistoryResponse,
  GeoHeatmapResponse,
  GeoLocationsResponse,
  ApiResponse
} from '@/types/adAnalysis'

// API 基础配置
const API_BASE_URL = '/api/ad-tracking/ad-analysis'

// 创建 axios 实例
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 可以在这里添加认证 token
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    const { data } = response
    console.log('[adAnalysisApi] Response:', {
      url: response.config.url,
      status: response.status,
      errCode: data.err_code,
      errMsg: data.err_msg
    })
    if (data.err_code !== 0) {
      console.error('API Error:', data.err_msg)
      return Promise.reject(new Error(data.err_msg || '请求失败'))
    }
    return data
  },
  (error) => {
    console.error('Network Error:', error)
    return Promise.reject(error)
  }
)

// ============ 黑词分析相关 API ============

/**
 * 获取黑词分析数据（圆环图、折线图、表格）
 */
export function apiGetDarkKeywordsAnalysis(params: Partial<AnalysisFilters>) {
  return api.get<any, ApiResponse<DarkKeywordsAnalysisResponse>>(
    '/dark-keywords',
    { params }
  )
}

/**
 * 获取黑词分类列表
 */
export function apiGetDarkKeywordCategories() {
  return api.get<any, ApiResponse<{ categories: DarkKeywordCategory[] }>>(
    '/dark-keywords/categories'
  )
}

/**
 * 删除黑词
 */
export function apiDeleteDarkKeyword(id: number) {
  return api.delete<any, ApiResponse<{ success: boolean }>>(
    `/dark-keywords/${id}`
  )
}

// ============ 交易方式相关 API ============

/**
 * 获取交易方式统计数据
 */
export function apiGetTransactionMethods(params: Partial<AnalysisFilters>) {
  return api.get<any, ApiResponse<TransactionMethodsResponse>>(
    '/transaction-methods',
    { params }
  )
}

/**
 * 获取交易方式趋势数据
 */
export function apiGetTransactionMethodsTrend(params: Partial<AnalysisFilters>) {
  return api.get<any, ApiResponse<TransactionMethodsTrendResponse>>(
    '/transaction-methods/trend',
    { params }
  )
}

/**
 * 获取交易方式列表
 */
export function apiGetTransactionMethodsList() {
  return api.get<any, ApiResponse<{ methods: Array<{ id: number; name: string }> }>>(
    '/transaction-methods/list'
  )
}

// ============ 价格趋势相关 API ============

/**
 * 获取价格趋势数据
 */
export function apiGetPriceTrend(params: Partial<AnalysisFilters>) {
  return api.get<any, ApiResponse<PriceTrendResponse>>(
    '/price-trend',
    { params }
  )
}

/**
 * 获取价格历史记录
 */
export function apiGetPriceHistory(params: Partial<AnalysisFilters>) {
  return api.get<any, ApiResponse<PriceHistoryResponse>>(
    '/price-history',
    { params }
  )
}

// ============ 热点地区相关 API ============

/**
 * 获取地理位置热力图数据
 */
export function apiGetGeoHeatmap(params: Partial<AnalysisFilters>) {
  return api.get<any, ApiResponse<GeoHeatmapResponse>>(
    '/geo-heatmap',
    { params }
  )
}

/**
 * 获取地理位置记录列表
 */
export function apiGetGeoLocations(params: Partial<AnalysisFilters>) {
  return api.get<any, ApiResponse<GeoLocationsResponse>>(
    '/geo-records',
    { params }
  )
}

// ============ 数据分析批处理 API ============

/**
 * 提交数据分析批处理任务
 */
export function apiSubmitAnalysisBatch(params: {
  chat_id: string
  include_price?: boolean
  include_transaction?: boolean
  include_geo?: boolean
  days?: number
}) {
  return api.post<any, any>('/batch/submit', params)
}

/**
 * 获取批次处理状态
 */
export function apiGetBatchStatus(batchId: string) {
  return api.get<any, any>(`/batch/${batchId}`)
}

/**
 * 获取批次列表
 */
export function apiGetBatchesList(params?: {
  chat_id?: string | number
  status?: string
  offset?: number
  limit?: number
}) {
  return api.get<any, any>('/batch', { params })
}

/**
 * 获取任务状态（Celery 任务）
 */
export function apiGetTaskStatus(taskId: string) {
  return api.get<any, any>(`/task/${taskId}`)
}

/**
 * 清除分析缓存
 *
 * 数据处理完成后调用，强制清除缓存以确保显示最新数据
 */
export function apiClearAnalysisCache(chatId?: string) {
  return api.post<any, ApiResponse<{
    message: string
    cleared_count: number
    cleared_keys: string[]
  }>>('/cache/clear', chatId ? { chat_id: chatId } : {})
}

// ============ 黑词配置管理 API ============

// 配置管理 API 基础 URL
const CONFIG_API_BASE_URL = '/api/config'

// 创建配置管理 axios 实例
const configApi = axios.create({
  baseURL: CONFIG_API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 响应拦截器
configApi.interceptors.response.use(
  (response) => {
    const { data } = response
    if (data.err_code !== 0) {
      console.error('Config API Error:', data.err_msg)
      return Promise.reject(new Error(data.err_msg || '请求失败'))
    }
    return data
  },
  (error) => {
    console.error('Network Error:', error)
    return Promise.reject(error)
  }
)

/**
 * 获取黑词分类列表（配置管理）
 */
export function apiGetDarkKeywordCategoriesConfig(params?: {
  is_active?: boolean
  offset?: number
  limit?: number
}) {
  return configApi.get<any, ApiResponse<any>>('/dark-keywords/categories', { params })
}

/**
 * 创建黑词分类
 */
export function apiCreateDarkKeywordCategory(data: {
  name: string
  display_name?: string
  description?: string
  priority?: number
  is_active?: boolean
}) {
  return configApi.post<any, ApiResponse<{ id: number }>>('/dark-keywords/categories', data)
}

/**
 * 更新黑词分类
 */
export function apiUpdateDarkKeywordCategory(
  id: number,
  data: {
    display_name?: string
    description?: string
    priority?: number
    is_active?: boolean
  }
) {
  return configApi.put<any, ApiResponse<any>>(`/dark-keywords/categories/${id}`, data)
}

/**
 * 删除黑词分类
 */
export function apiDeleteDarkKeywordCategory(id: number) {
  return configApi.delete<any, ApiResponse<{ id: number }>>(`/dark-keywords/categories/${id}`)
}

/**
 * 获取毒品列表（配置管理）
 */
export function apiGetDarkKeywordDrugs(params?: {
  category_id?: number
  is_active?: boolean
  offset?: number
  limit?: number
}) {
  return configApi.get<any, ApiResponse<any>>('/dark-keywords/drugs', { params })
}

/**
 * 创建毒品
 */
export function apiCreateDarkKeywordDrug(data: {
  category_id: number
  name: string
  display_name?: string
  description?: string
  priority?: number
  is_active?: boolean
}) {
  return configApi.post<any, ApiResponse<{ id: number }>>('/dark-keywords/drugs', data)
}

/**
 * 更新毒品
 */
export function apiUpdateDarkKeywordDrug(
  id: number,
  data: {
    display_name?: string
    description?: string
    priority?: number
    is_active?: boolean
  }
) {
  return configApi.put<any, ApiResponse<any>>(`/dark-keywords/drugs/${id}`, data)
}

/**
 * 删除毒品
 */
export function apiDeleteDarkKeywordDrug(id: number) {
  return configApi.delete<any, ApiResponse<{ id: number }>>(`/dark-keywords/drugs/${id}`)
}

/**
 * 获取毒品的关键词列表
 */
export function apiGetDarkKeywordsByDrug(drugId: number) {
  return configApi.get<any, ApiResponse<any>>(`/dark-keywords/drugs/${drugId}/keywords`)
}

/**
 * 创建关键词
 */
export function apiCreateDarkKeyword(data: {
  drug_id: number
  keyword: string
  weight?: number
  is_active?: boolean
}) {
  return configApi.post<any, ApiResponse<{ id: number }>>('/dark-keywords/keywords', data)
}

/**
 * 更新关键词
 */
export function apiUpdateDarkKeyword(
  id: number,
  data: {
    weight?: number
    is_active?: boolean
  }
) {
  return configApi.put<any, ApiResponse<any>>(`/dark-keywords/keywords/${id}`, data)
}

/**
 * 删除关键词
 */
export function apiDeleteDarkKeywordConfig(id: number) {
  return configApi.delete<any, ApiResponse<{ id: number }>>(`/dark-keywords/keywords/${id}`)
}

export default api
