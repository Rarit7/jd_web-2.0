/**
 * 通用分页管理组合式函数
 * 可复用于应用中的所有分页场景
 */

import { ref, computed } from 'vue'

/**
 * 分页选项接口
 */
export interface PaginationOptions {
  defaultPageSize?: number
  pageSizes?: number[]
  onPageChange?: (page: number, pageSize: number) => void | Promise<void>
}

/**
 * 通用分页状态管理
 */
export function usePagination(options: PaginationOptions = {}) {
  const {
    defaultPageSize = 20,
    pageSizes = [20, 40, 60, 100],
    onPageChange
  } = options

  // 状态
  const currentPage = ref(1)
  const pageSize = ref(defaultPageSize)
  const total = ref(0)

  /**
   * 总页数
   */
  const totalPages = computed(() => Math.ceil(total.value / pageSize.value) || 1)

  /**
   * 是否有下一页
   */
  const hasNextPage = computed(() => currentPage.value < totalPages.value)

  /**
   * 是否有上一页
   */
  const hasPrevPage = computed(() => currentPage.value > 1)

  /**
   * 当前页的起始索引（从 1 开始）
   */
  const startIndex = computed(() =>
    (currentPage.value - 1) * pageSize.value + 1
  )

  /**
   * 当前页的结束索引
   */
  const endIndex = computed(() =>
    Math.min(currentPage.value * pageSize.value, total.value)
  )

  /**
   * 设置当前页码
   */
  const setPage = (page: number): void => {
    const validPage = Math.max(1, Math.min(page, totalPages.value))
    currentPage.value = validPage
    onPageChange?.(validPage, pageSize.value)
  }

  /**
   * 设置每页数量
   */
  const setPageSize = (size: number): void => {
    pageSize.value = size
    currentPage.value = 1 // 重置到第一页
    onPageChange?.(1, size)
  }

  /**
   * 重置分页状态
   */
  const reset = (): void => {
    currentPage.value = 1
    pageSize.value = defaultPageSize
  }

  /**
   * 下一页
   */
  const nextPage = (): void => {
    if (hasNextPage.value) {
      setPage(currentPage.value + 1)
    }
  }

  /**
   * 上一页
   */
  const prevPage = (): void => {
    if (hasPrevPage.value) {
      setPage(currentPage.value - 1)
    }
  }

  return {
    // 状态
    currentPage,
    pageSize,
    total,
    pageSizes,
    // 计算属性
    totalPages,
    hasNextPage,
    hasPrevPage,
    startIndex,
    endIndex,
    // 方法
    setPage,
    setPageSize,
    reset,
    nextPage,
    prevPage
  }
}
