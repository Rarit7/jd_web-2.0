/**
 * 广告追踪 API 服务
 */
import request from './request'
import type {
  ApiResponse,
  AdTracking,
  AdTrackingDetail,
  AdTrackingListParams,
  AdTrackingListResponse,
  SearchByDomainParams,
  SearchByDomainResponse,
  StatsParams,
  StatsResponse,
  ExecuteTaskParams,
  ExecuteTaskResponse,
  TaskStatusResponse,
  AddTagsParams,
  AddTagsResponse,
  DeleteResponse
} from '@/types/adTracking'

const BASE_PATH = '/ad-tracking'

/**
 * 获取广告追踪列表
 */
export function getAdTrackingList(params: AdTrackingListParams) {
  return request<ApiResponse<AdTrackingListResponse>>({
    url: `${BASE_PATH}/list`,
    method: 'get',
    params
  })
}

/**
 * 获取广告追踪详情
 */
export function getAdTrackingDetail(trackingId: number) {
  return request<ApiResponse<AdTrackingDetail>>({
    url: `${BASE_PATH}/${trackingId}`,
    method: 'get'
  })
}

/**
 * 按域名搜索
 */
export function searchByDomain(params: SearchByDomainParams) {
  return request<ApiResponse<SearchByDomainResponse>>({
    url: `${BASE_PATH}/search-by-domain`,
    method: 'get',
    params
  })
}

/**
 * 获取统计信息
 */
export function getStats(params?: StatsParams) {
  return request<ApiResponse<StatsResponse>>({
    url: `${BASE_PATH}/stats`,
    method: 'get',
    params
  })
}

/**
 * 执行追踪任务
 */
export function executeTask(data: ExecuteTaskParams) {
  return request<ApiResponse<ExecuteTaskResponse>>({
    url: `${BASE_PATH}/task/execute`,
    method: 'post',
    data
  })
}

/**
 * 查询任务状态
 */
export function getTaskStatus(taskId: string) {
  return request<ApiResponse<TaskStatusResponse>>({
    url: `${BASE_PATH}/task/status/${taskId}`,
    method: 'get'
  })
}

/**
 * 为追踪记录添加标签
 */
export function addTags(trackingId: number, data: AddTagsParams) {
  return request<ApiResponse<AddTagsResponse>>({
    url: `${BASE_PATH}/tags/${trackingId}`,
    method: 'post',
    data
  })
}

/**
 * 删除追踪记录的标签
 */
export function deleteTag(trackingId: number, tagId: number) {
  return request<ApiResponse<DeleteResponse>>({
    url: `${BASE_PATH}/tags/${trackingId}/${tagId}`,
    method: 'delete'
  })
}

/**
 * 删除广告追踪记录
 */
export function deleteAdTracking(trackingId: number) {
  return request<ApiResponse<DeleteResponse>>({
    url: `${BASE_PATH}/${trackingId}`,
    method: 'delete'
  })
}

/**
 * 更新商家名称
 */
export function updateMerchantName(trackingId: number, merchantName: string) {
  return request<ApiResponse<{ message: string; merchant_name: string | null }>>({
    url: `${BASE_PATH}/${trackingId}/merchant-name`,
    method: 'put',
    data: { merchant_name: merchantName }
  })
}

// ==================== 高价值信息 API ====================

interface HighValueMessageListParams {
  page?: number
  page_size?: number
  user_id?: string
  chat_id?: string
  is_high_priority?: number
  start_date?: string
  end_date?: string
  search?: string
  sort_by?: 'importance_score' | 'publish_time' | 'created_at'
  sort_order?: 'asc' | 'desc'
}

interface HighValueMessageListResponse {
  data: any[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

/**
 * 获取高价值信息列表
 */
export function getHighValueMessages(params: HighValueMessageListParams) {
  return request<ApiResponse<HighValueMessageListResponse>>({
    url: `${BASE_PATH}/high-value-messages`,
    method: 'get',
    params
  })
}

/**
 * 获取单个高价值信息详情
 */
export function getHighValueMessage(messageId: number) {
  return request<ApiResponse<{ data: any }>>({
    url: `${BASE_PATH}/high-value-messages/${messageId}`,
    method: 'get'
  })
}

/**
 * 删除高价值信息
 */
export function deleteHighValueMessage(messageId: number) {
  return request<ApiResponse<null>>({
    url: `${BASE_PATH}/high-value-messages/${messageId}`,
    method: 'delete'
  })
}

/**
 * 导出API对象（兼容旧代码风格）
 */
export const adTrackingApi = {
  getList: getAdTrackingList,
  getDetail: getAdTrackingDetail,
  searchByDomain,
  getStats,
  executeTask,
  getTaskStatus,
  addTags,
  deleteTag,
  delete: deleteAdTracking,
  updateMerchantName,
  // 高价值信息 API
  getHighValueMessages,
  getHighValueMessage,
  deleteHighValueMessage
}

export default adTrackingApi
