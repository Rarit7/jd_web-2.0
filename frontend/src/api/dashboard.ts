import request from './request'
import type { ApiResponse } from '@/types/api'

export interface DashboardStatistics {
  group_count: number
  user_count: number
  message_count: number
  blackword_count: number
}

export const dashboardApi = {
  /**
   * 获取首页统计数据
   */
  getStatistics: () => {
    return request.get<ApiResponse<DashboardStatistics>>('/dashboard/statistics')
  }
}