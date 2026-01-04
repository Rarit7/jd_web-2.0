/**
 * Ad Tracking 记录数据管理组合式函数
 * 处理所有数据加载、CRUD 操作和状态管理
 */

import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import adTrackingApi from '@/api/adTracking'
import type { AdTrackingRecord, AdTrackingChannel, AdTrackingTag } from '@/types/adTracking'

/**
 * 记录查询参数接口
 */
export interface RecordsFilterParams {
  page: number
  page_size: number
  channel_id?: number
  trigger_tag_id?: number
  is_processed?: boolean
}

/**
 * 导出参数接口
 */
export interface ExportRecordsParams {
  format: 'excel' | 'csv'
  channel_id?: number
  trigger_tag_id?: number
  is_processed?: boolean
}

/**
 * 管理广告追踪记录的数据操作
 */
export function useAdRecords() {
  // 加载状态
  const loading = ref(false)

  // 数据状态
  const records = ref<AdTrackingRecord[]>([])
  const channels = ref<AdTrackingChannel[]>([])
  const tags = ref<AdTrackingTag[]>([])
  const total = ref(0)

  /**
   * 只显示频道类型的数据（不显示群组）
   * group_type: 1 = 群组, 2 = 频道
   */
  const filteredChannels = computed(() =>
    channels.value.filter(channel => channel.group_type === 2)
  )

  /**
   * 加载广告记录（分页）
   */
  const loadRecords = async (params: RecordsFilterParams): Promise<void> => {
    try {
      const response = await adTrackingApi.getRecords(params)
      records.value = response.data || []
      total.value = response.total || 0
    } catch (error) {
      ElMessage.error('加载记录失败')
      throw error
    }
  }

  /**
   * 加载频道列表
   */
  const loadChannels = async (): Promise<void> => {
    try {
      const response = await adTrackingApi.getChannels()
      channels.value = response.data || []
    } catch (error) {
      ElMessage.error('加载频道失败')
      throw error
    }
  }

  /**
   * 加载标签列表
   */
  const loadTags = async (): Promise<void> => {
    try {
      const response = await adTrackingApi.getTags()
      tags.value = response.data || []
    } catch (error) {
      ElMessage.error('加载标签失败')
      throw error
    }
  }

  /**
   * 并行加载所有数据（记录、频道、标签）
   */
  const loadAllData = async (params: RecordsFilterParams): Promise<void> => {
    loading.value = true
    try {
      // 并行加载所有数据以提高性能
      const [recordsRes, channelsRes, tagsRes] = await Promise.all([
        adTrackingApi.getRecords(params),
        adTrackingApi.getChannels(),
        adTrackingApi.getTags()
      ])

      records.value = recordsRes.data || []
      total.value = recordsRes.total || 0
      channels.value = channelsRes.data || []
      tags.value = tagsRes.data || []
    } catch (error) {
      ElMessage.error('加载数据失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  /**
   * 更新单条记录
   */
  const updateRecord = async (
    id: number,
    data: Partial<AdTrackingRecord>
  ): Promise<void> => {
    try {
      await adTrackingApi.updateRecord(id, data)
    } catch (error) {
      ElMessage.error('更新记录失败')
      throw error
    }
  }

  /**
   * 删除单条记录
   */
  const deleteRecord = async (id: number): Promise<void> => {
    try {
      await adTrackingApi.deleteRecord(id)
    } catch (error) {
      ElMessage.error('删除记录失败')
      throw error
    }
  }

  /**
   * 导出记录（返回 Blob）
   */
  const exportRecords = async (params: ExportRecordsParams): Promise<Blob> => {
    try {
      const response = await adTrackingApi.exportRecords(params)
      return new Blob([response])
    } catch (error) {
      ElMessage.error('导出记录失败')
      throw error
    }
  }

  return {
    // 状态
    loading,
    records,
    channels,
    tags,
    total,
    // 计算属性
    filteredChannels,
    // 方法
    loadRecords,
    loadChannels,
    loadTags,
    loadAllData,
    updateRecord,
    deleteRecord,
    exportRecords
  }
}
