/**
 * 广告追踪 Pinia Store
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { adTrackingApi } from '@/api/adTracking'
import type {
  AdTracking,
  AdTrackingDetail,
  FilterConditions,
  Pagination,
  StatsResponse,
  ContentType,
  SourceType
} from '@/types/adTracking'

export const useAdTrackingStore = defineStore('adTracking', () => {
  // ==================== State ====================

  // 列表数据
  const trackingList = ref<AdTracking[]>([])
  const currentDetail = ref<AdTrackingDetail | null>(null)

  // 统计数据
  const stats = ref<StatsResponse | null>(null)

  // 筛选条件
  const filters = ref<FilterConditions>({
    contentTypes: [],
    sourceTypes: [],
    tagIds: [],
    dateRange: null,
    search: '',
    userId: '',
    chatId: '',
    domain: '',
    sortBy: 'last_seen',
    sortOrder: 'desc'
  })

  // 分页
  const pagination = ref<Pagination>({
    page: 1,
    pageSize: 20,
    total: 0
  })

  // 加载状态
  const loading = ref({
    list: false,
    detail: false,
    stats: false
  })

  // 详情侧边栏显示状态
  const showDetailDrawer = ref(false)

  // ==================== Computed ====================

  const totalPages = computed(() =>
    Math.ceil(pagination.value.total / pagination.value.pageSize)
  )

  const hasFilters = computed(() => {
    return (
      filters.value.contentTypes.length > 0 ||
      filters.value.sourceTypes.length > 0 ||
      filters.value.tagIds.length > 0 ||
      filters.value.dateRange !== null ||
      filters.value.search !== '' ||
      filters.value.userId !== '' ||
      filters.value.chatId !== '' ||
      filters.value.domain !== ''
    )
  })

  // ==================== Actions ====================

  /**
   * 获取广告追踪列表
   */
  async function fetchTrackingList(resetPage = false) {
    if (resetPage) {
      pagination.value.page = 1
    }

    loading.value.list = true

    try {
      const params: any = {
        page: pagination.value.page,
        page_size: pagination.value.pageSize,
        sort_by: filters.value.sortBy,
        sort_order: filters.value.sortOrder
      }

      // 添加筛选条件
      if (filters.value.contentTypes.length > 0) {
        params.content_type = filters.value.contentTypes[0] // API目前只支持单个类型
      }
      if (filters.value.sourceTypes.length > 0) {
        params.source_type = filters.value.sourceTypes[0]
      }
      if (filters.value.search) {
        params.search = filters.value.search
      }
      if (filters.value.userId) {
        params.user_id = filters.value.userId
      }
      if (filters.value.chatId) {
        params.chat_id = filters.value.chatId
      }
      if (filters.value.dateRange && filters.value.dateRange.length === 2) {
        params.start_date = filters.value.dateRange[0]
        params.end_date = filters.value.dateRange[1]
      }

      const response = await adTrackingApi.getList(params)

      if (response.data.err_code === 0) {
        const payload = response.data.payload
        trackingList.value = payload.data
        pagination.value.total = payload.total
        pagination.value.page = payload.page
        pagination.value.pageSize = payload.page_size
      } else {
        ElMessage.error(response.data.err_msg || '获取列表失败')
      }
    } catch (error: any) {
      console.error('获取广告追踪列表失败:', error)
      ElMessage.error(error.message || '获取列表失败')
    } finally {
      loading.value.list = false
    }
  }

  /**
   * 获取广告追踪详情
   */
  async function fetchTrackingDetail(trackingId: number) {
    loading.value.detail = true

    try {
      const response = await adTrackingApi.getDetail(trackingId)

      if (response.data.err_code === 0) {
        currentDetail.value = response.data.payload
        showDetailDrawer.value = true
      } else {
        ElMessage.error(response.data.err_msg || '获取详情失败')
      }
    } catch (error: any) {
      console.error('获取广告追踪详情失败:', error)
      ElMessage.error(error.message || '获取详情失败')
    } finally {
      loading.value.detail = false
    }
  }

  /**
   * 获取统计数据
   */
  async function fetchStats(startDate?: string, endDate?: string) {
    loading.value.stats = true

    try {
      const params: any = {}
      if (startDate) params.start_date = startDate
      if (endDate) params.end_date = endDate

      const response = await adTrackingApi.getStats(params)

      if (response.data.err_code === 0) {
        stats.value = response.data.payload
      } else {
        ElMessage.error(response.data.err_msg || '获取统计失败')
      }
    } catch (error: any) {
      console.error('获取统计数据失败:', error)
      ElMessage.error(error.message || '获取统计失败')
    } finally {
      loading.value.stats = false
    }
  }

  /**
   * 按域名搜索
   */
  async function searchByDomain(domain: string) {
    loading.value.list = true

    try {
      const response = await adTrackingApi.searchByDomain({
        domain,
        page: pagination.value.page,
        page_size: pagination.value.pageSize
      })

      if (response.data.err_code === 0) {
        const payload = response.data.payload
        trackingList.value = payload.data
        pagination.value.total = payload.total
        pagination.value.page = payload.page
        pagination.value.pageSize = payload.page_size
      } else {
        ElMessage.error(response.data.err_msg || '搜索失败')
      }
    } catch (error: any) {
      console.error('按域名搜索失败:', error)
      ElMessage.error(error.message || '搜索失败')
    } finally {
      loading.value.list = false
    }
  }

  /**
   * 添加标签
   */
  async function addTags(trackingId: number, tagIds: number[]) {
    try {
      const response = await adTrackingApi.addTags(trackingId, { tag_ids: tagIds })

      if (response.data.err_code === 0) {
        ElMessage.success(response.data.payload.message)

        // 刷新当前详情（如果是当前打开的记录）
        if (currentDetail.value?.id === trackingId) {
          await fetchTrackingDetail(trackingId)
        }

        // 刷新列表
        await fetchTrackingList()

        return true
      } else {
        ElMessage.error(response.data.err_msg || '添加标签失败')
        return false
      }
    } catch (error: any) {
      console.error('添加标签失败:', error)
      ElMessage.error(error.message || '添加标签失败')
      return false
    }
  }

  /**
   * 删除标签
   */
  async function deleteTag(trackingId: number, tagId: number) {
    try {
      const response = await adTrackingApi.deleteTag(trackingId, tagId)

      if (response.data.err_code === 0) {
        ElMessage.success('删除成功')

        // 刷新当前详情
        if (currentDetail.value?.id === trackingId) {
          await fetchTrackingDetail(trackingId)
        }

        // 刷新列表
        await fetchTrackingList()

        return true
      } else {
        ElMessage.error(response.data.err_msg || '删除标签失败')
        return false
      }
    } catch (error: any) {
      console.error('删除标签失败:', error)
      ElMessage.error(error.message || '删除标签失败')
      return false
    }
  }

  /**
   * 删除广告追踪记录
   */
  async function deleteTracking(trackingId: number) {
    try {
      const response = await adTrackingApi.delete(trackingId)

      if (response.data.err_code === 0) {
        ElMessage.success('删除成功')

        // 关闭详情侧边栏
        if (currentDetail.value?.id === trackingId) {
          showDetailDrawer.value = false
          currentDetail.value = null
        }

        // 刷新列表
        await fetchTrackingList()

        return true
      } else {
        ElMessage.error(response.data.err_msg || '删除失败')
        return false
      }
    } catch (error: any) {
      console.error('删除广告追踪记录失败:', error)
      ElMessage.error(error.message || '删除失败')
      return false
    }
  }

  /**
   * 更新商家名称
   */
  async function updateMerchantName(trackingId: number, merchantName: string) {
    try {
      const response = await adTrackingApi.updateMerchantName(trackingId, merchantName)

      if (response.data.err_code === 0) {
        // 更新详情中的商家名称
        if (currentDetail.value?.id === trackingId) {
          currentDetail.value.merchant_name = response.data.payload.merchant_name
        }

        // 更新列表中的商家名称
        const listItem = trackingList.value.find(item => item.id === trackingId)
        if (listItem) {
          listItem.merchant_name = response.data.payload.merchant_name
        }

        return true
      } else {
        ElMessage.error(response.data.err_msg || '更新失败')
        return false
      }
    } catch (error: any) {
      console.error('更新商家名称失败:', error)
      ElMessage.error(error.message || '更新失败')
      return false
    }
  }

  /**
   * 更新筛选条件
   */
  function updateFilters(newFilters: Partial<FilterConditions>) {
    filters.value = {
      ...filters.value,
      ...newFilters
    }
  }

  /**
   * 重置筛选条件
   */
  function resetFilters() {
    filters.value = {
      contentTypes: [],
      sourceTypes: [],
      tagIds: [],
      dateRange: null,
      search: '',
      userId: '',
      chatId: '',
      domain: '',
      sortBy: 'last_seen',
      sortOrder: 'desc'
    }
    pagination.value.page = 1
  }

  /**
   * 设置页码
   */
  function setPage(page: number) {
    pagination.value.page = page
  }

  /**
   * 设置每页数量
   */
  function setPageSize(pageSize: number) {
    pagination.value.pageSize = pageSize
    pagination.value.page = 1
  }

  /**
   * 设置详情数据
   */
  function setDetailDrawerData(data: any) {
    currentDetail.value = data
  }

  /**
   * 打开详情侧边栏
   */
  function openDetailDrawer() {
    showDetailDrawer.value = true
  }

  /**
   * 关闭详情侧边栏
   */
  function closeDetailDrawer() {
    showDetailDrawer.value = false
    currentDetail.value = null
  }

  /**
   * 执行任务
   */
  async function executeTask(taskParams: any) {
    try {
      const response = await adTrackingApi.executeTask(taskParams)

      if (response.data.err_code === 0) {
        ElMessage.success('任务已提交')
        return response.data.payload
      } else {
        ElMessage.error(response.data.err_msg || '任务提交失败')
        return null
      }
    } catch (error: any) {
      console.error('执行任务失败:', error)
      ElMessage.error(error.message || '任务提交失败')
      return null
    }
  }

  /**
   * 查询任务状态
   */
  async function getTaskStatus(taskId: string) {
    try {
      const response = await adTrackingApi.getTaskStatus(taskId)

      if (response.data.err_code === 0) {
        return response.data.payload
      } else {
        ElMessage.error(response.data.err_msg || '查询任务状态失败')
        return null
      }
    } catch (error: any) {
      console.error('查询任务状态失败:', error)
      ElMessage.error(error.message || '查询任务状态失败')
      return null
    }
  }

  return {
    // State
    trackingList,
    currentDetail,
    stats,
    filters,
    pagination,
    loading,
    showDetailDrawer,

    // Computed
    totalPages,
    hasFilters,

    // Actions
    fetchTrackingList,
    fetchTrackingDetail,
    fetchStats,
    searchByDomain,
    addTags,
    deleteTag,
    deleteTracking,
    updateMerchantName,
    updateFilters,
    resetFilters,
    setPage,
    setPageSize,
    setDetailDrawerData,
    openDetailDrawer,
    closeDetailDrawer,
    executeTask,
    getTaskStatus
  }
})
