/**
 * 数据分析系统 (Ad Analysis) 类型定义
 */

// ============ 黑词分析类型 ============
export interface DarkKeywordData {
  id: number
  keyword: string
  category_id?: number
  category?: string
  drug_id?: number
  drug_name?: string
  count: number
  last_updated?: string
}

export interface DarkKeywordsPieData {
  name: string
  value: number
}

export interface DarkKeywordsTrendData {
  months: string[]
  data: Record<string, number[]>
}

export interface DarkKeywordCategory {
  id: number
  name: string
  drugs?: Array<{
    id: number
    name: string
  }>
}

// ============ 交易方式类型 ============
export interface TransactionMethodData {
  id: number
  name: string
  count?: number
  value?: number  // 后端返回 value 而不是 count
  percentage?: number
  trend?: number
}

export interface TransactionMethodTrendData {
  months: string[]
  data: Record<string, number[]>
}

// ============ 价格趋势类型 ============
export interface PriceTrendData {
  months: string[]
  data: Record<string, number[]>
}

export interface PriceHistoryRecord {
  id: number
  product_name?: string
  unit?: string
  price: number
  date?: string
  created_at?: string
}

export interface PriceTrendStatistics {
  max_price: number
  min_price: number
  avg_price: number
  price_change: number
}

// ============ 地理位置类型 ============
export interface GeoLocationData {
  id?: number
  province: string
  city?: string
  count?: number
  percentage?: number
  coordinates?: [number, number]
  msg_date?: string
  [key: string]: any  // 允许模型返回的其他字段
}

export interface GeoHeatmapData {
  name: string
  value: number
}

export interface GeoLocationStatistics {
  total_locations: number
  provinces_count: number
  cities_count: number
}

export interface ShandongCityData {
  name: string
  count: number
}

// ============ 分析通用类型 ============
export interface AnalysisFilters {
  chat_id: number
  tag_ids?: number[]
  keyword?: string
  category?: number
  drug?: number
  province?: string
  city?: string
  days?: number
  offset?: number
  limit?: number
}

export interface AnalysisApiResponse<T> {
  err_code: number
  err_msg: string
  payload: {
    data?: T
    total?: number
    page?: number
    page_size?: number
    [key: string]: any
  }
}

export interface PaginatedResponse<T> {
  data: T[]
  total: number
  page: number
  page_size: number
}

// ============ 黑词分析 API 响应 ============
export interface DarkKeywordsAnalysisResponse {
  pie: DarkKeywordsPieData[]
  line: DarkKeywordsTrendData
  table: DarkKeywordData[]
  total: number
  page?: number
  page_size?: number
}

// ============ 交易方式 API 响应 ============
export interface TransactionMethodsResponse {
  bar: Array<{
    name: string
    value: number
    id: number
  }>
}

export interface TransactionMethodsTrendResponse {
  line: {
    months: string[]
    data: Record<string, number[]>
  }
}

// ============ 价格趋势 API 响应 ============
// 后端直接返回 {months, data}，统计信息由前端计算
export interface PriceTrendResponse {
  months: string[]
  data: Record<string, number[]>
}

export interface PriceHistoryResponse {
  data: PriceHistoryRecord[]
  total: number
  page?: number
  page_size?: number
}

// ============ 地理位置 API 响应 ============
export interface GeoHeatmapResponse {
  provinces: Array<{
    name: string
    value: number
  }>
  shandong_cities?: Array<{
    name: string
    value: number
  }>
  all_cities: Array<{
    name: string
    value: number
    province: string
  }>
}

export interface GeoLocationsResponse {
  data: Array<{
    province: string
    city?: string
    count?: number
    [key: string]: any
  }>
  total: number
  page?: number
  page_size?: number
}

// ============ 统一的 API 响应数据 ============
export type ApiResponse<T> = AnalysisApiResponse<T>
