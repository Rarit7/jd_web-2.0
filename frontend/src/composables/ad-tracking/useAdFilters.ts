/**
 * Ad Tracking 筛选状态管理组合式函数
 */

import { ref, computed } from 'vue'

/**
 * 筛选条件状态接口
 */
export interface FilterState {
  channel_id: number | null
  trigger_tag_id: number | null
  is_processed: boolean | null
}

/**
 * API 请求参数接口
 */
export interface FiltersApiParams {
  channel_id?: number
  trigger_tag_id?: number
  is_processed?: boolean
}

/**
 * 管理广告追踪的筛选状态和逻辑
 */
export function useAdFilters(initialFilters?: Partial<FilterState>) {
  // 筛选条件状态
  const filters = ref<FilterState>({
    channel_id: null,
    trigger_tag_id: null,
    is_processed: null,
    ...initialFilters
  })

  /**
   * 设置单个筛选条件
   */
  const setFilter = <K extends keyof FilterState>(key: K, value: FilterState[K]): void => {
    filters.value[key] = value
  }

  /**
   * 重置所有筛选条件
   */
  const resetFilters = (): void => {
    filters.value = {
      channel_id: null,
      trigger_tag_id: null,
      is_processed: null
    }
  }

  /**
   * 转换筛选条件为 API 参数格式（只包含非空值）
   */
  const toApiParams = (): FiltersApiParams => {
    const params: FiltersApiParams = {}

    if (filters.value.channel_id !== null) {
      params.channel_id = filters.value.channel_id
    }

    if (filters.value.trigger_tag_id !== null) {
      params.trigger_tag_id = filters.value.trigger_tag_id
    }

    if (filters.value.is_processed !== null) {
      params.is_processed = filters.value.is_processed
    }

    return params
  }

  /**
   * 是否有活跃的筛选条件
   */
  const hasActiveFilters = computed(() =>
    Object.values(filters.value).some(v => v !== null)
  )

  /**
   * 活跃筛选条件的数量
   */
  const filterCount = computed(() =>
    Object.values(filters.value).filter(v => v !== null).length
  )

  return {
    // 状态
    filters,
    // 计算属性
    hasActiveFilters,
    filterCount,
    // 方法
    setFilter,
    resetFilters,
    toApiParams
  }
}
