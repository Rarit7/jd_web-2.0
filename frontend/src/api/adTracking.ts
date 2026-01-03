/**
 * 广告追踪记录管理 API 服务
 */
import axios from 'axios'
import type {
  AdTrackingRecord,
  AdTrackingRecordDetail,
  AdTrackingChannel,
  AdTrackingTag,
  AdTrackingBatch,
  RelatedRecord,
  RecordsFilterParams,
  ChannelsQueryParams,
  TagsQueryParams,
  HistoryQueryParams,
  StartProcessingParams,
  ExportRecordsParams,
  StatisticsData,
  BatchSummary,
  ChannelProcessingStatus
} from '@/types/adTracking'

// API 基础配置
const API_BASE_URL = '/api/ad-tracking'

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
    console.log('[adTrackingApi] Response interceptor:', {
      url: response.config.url,
      status: response.status,
      errCode: data.err_code,
      errMsg: data.err_msg,
      hasPayload: !!data.payload,
      payloadKeys: data.payload ? Object.keys(data.payload) : []
    })
    if (data.err_code !== 0) {
      console.error('API Error:', data.err_msg)
      return Promise.reject(new Error(data.err_msg || '请求失败'))
    }
    return data
  },
  (error) => {
    console.error('Network Error:', error)
    console.error('[adTrackingApi] Error details:', {
      message: error.message,
      config: error.config?.url,
      status: error.response?.status,
      responseData: error.response?.data
    })
    return Promise.reject(error)
  }
)

// 广告记录 API
export const adTrackingApi = {
  /**
   * 获取广告记录列表
   */
  getRecords: async (params: RecordsFilterParams) => {
    console.log('[adTrackingApi] getRecords called with params:', params)
    const response = await api.get('/records', { params })
    console.log('[adTrackingApi] getRecords response:', {
      total: response.payload?.total,
      dataCount: response.payload?.data?.length,
      pageSize: response.payload?.page_size,
      currentPage: response.payload?.page,
      fullResponse: response.payload
    })
    return response.payload
  },

  /**
   * 获取广告记录详情
   */
  getRecordDetail: async (recordId: number): Promise<AdTrackingRecordDetail> => {
    const response = await api.get(`/records/${recordId}`)
    return response.payload.data
  },

  /**
   * 删除广告记录
   */
  deleteRecord: async (recordId: number) => {
    await api.delete(`/records/${recordId}`)
  },

  /**
   * 批量删除广告记录
   */
  batchDeleteRecords: async (recordIds: number[]) => {
    const response = await api.post('/records/batch/delete', { record_ids: recordIds })
    return response.payload.data
  },

  /**
   * 搜索广告记录
   */
  searchRecords: async (keyword: string, searchType: string = 'all', limit: number = 50) => {
    const response = await api.get('/records/search', {
      params: { keyword, search_type: searchType, limit }
    })
    return response.payload
  },

  /**
   * 导出广告记录
   */
  exportRecords: async (params: ExportRecordsParams = {}): Promise<Blob> => {
    const response = await axios.get(`${API_BASE_URL}/records/export`, {
      params,
      responseType: 'blob'
    })
    return response.data
  },

  /**
   * 更新广告记录
   */
  updateRecord: async (recordId: number, data: Partial<AdTrackingRecord>) => {
    const response = await api.patch(`/records/${recordId}`, data)
    return response.payload
  }
}

// 频道管理 API
export const channelsApi = {
  /**
   * 获取频道列表
   */
  getChannels: async (params: ChannelsQueryParams = {}) => {
    const response = await api.get('/channels', { params })
    return response.payload
  },

  /**
   * 获取频道详情
   */
  getChannelInfo: async (channelId: number): Promise<AdTrackingChannel> => {
    const response = await api.get(`/channels/${channelId}`)
    return response.payload.data
  }
}

// 标签管理 API
export const tagsApi = {
  /**
   * 获取标签列表
   */
  getTags: async (params: TagsQueryParams = {}) => {
    const response = await api.get('/tags', { params })
    return response.payload
  },

  /**
   * 获取标签详情
   */
  getTagDetail: async (tagId: number) => {
    const response = await api.get(`/tags/${tagId}`)
    return response.payload.data
  }
}

// 处理管理 API
export const processingApi = {
  /**
   * 开始处理频道
   */
  startProcessing: async (params: StartProcessingParams) => {
    const response = await api.post('/process', params)
    return response.payload.data
  },

  /**
   * 获取处理状态
   */
  getBatchInfo: async (batchId: string): Promise<AdTrackingBatch> => {
    const response = await api.get(`/process/${batchId}`)
    return response.payload.data
  },

  /**
   * 取消处理任务
   */
  cancelBatch: async (batchId: string) => {
    await api.post(`/process/${batchId}/cancel`)
  },

  /**
   * 重试处理任务
   */
  retryBatch: async (batchId: string) => {
    const response = await api.post(`/process/retry/${batchId}`)
    return response.payload.data
  },

  /**
   * 获取处理历史
   */
  getHistory: async (params: HistoryQueryParams = {}) => {
    const response = await api.get('/process/history', { params })
    return response.payload
  }
}

// 统计分析 API
export const statisticsApi = {
  /**
   * 获取统计信息
   */
  getStatistics: async (days: number = 30) => {
    const response = await api.get('/statistics', {
      params: { days }
    })
    return response.payload.data as StatisticsData
  },

  /**
   * 获取频道消息数量
   */
  getChannelMessageCount: async (channelId: number, startDate?: string, endDate?: string) => {
    const response = await api.get('/channels/count', {
      params: { channel_id: channelId, start_date: startDate, end_date: endDate }
    })
    return response.payload.data
  }
}

// 服务方法 API（模拟后端服务方法）
export const serviceApi = {
  /**
   * 获取批次摘要
   */
  getBatchSummary: async (batchId: string): Promise<BatchSummary> => {
    const response = await api.get(`/service/batch-summary/${batchId}`)
    return response.payload.data
  },

  /**
   * 检查频道处理状态
   */
  checkChannelProcessingStatus: async (channelId: number): Promise<ChannelProcessingStatus> => {
    const response = await api.get('/service/processing-status', {
      params: { channel_id: channelId }
    })
    return response.payload.data
  },

  /**
   * 获取关联记录
   */
  getRelatedRecords: async (recordId: number, limit: number = 5) => {
    const response = await api.get(`/service/related-records/${recordId}`, {
      params: { limit }
    })
    return response.payload
  },

  /**
   * 获取重复记录
   */
  getDuplicateRecords: async (channelId: number, days: number = 7) => {
    const response = await api.get('/service/duplicate-records', {
      params: { channel_id: channelId, days }
    })
    return response.payload
  },

  /**
   * 批量更新记录状态
   */
  batchUpdateRecordsStatus: async (recordIds: number[], isProcessed: boolean) => {
    const response = await api.post('/service/batch-update-status', {
      record_ids: recordIds,
      is_processed: isProcessed
    })
    return response.payload.data
  }
}

// 导出默认 API 对象
export default {
  ...adTrackingApi,
  ...channelsApi,
  ...tagsApi,
  ...processingApi,
  ...statisticsApi,
  ...serviceApi
}