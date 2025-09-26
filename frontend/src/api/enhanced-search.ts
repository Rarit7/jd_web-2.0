/**
 * 增强搜索API - 支持简繁体转换
 */
import { tgGroupsApi, type TgGroupListParams, type TgGroup } from './tg-groups'
import { getSearchVariants, containsChinese } from '@/utils/chineseConverter'

/**
 * API响应数据结构（适配原始API格式）
 */
interface ApiResponse<T> {
  err_code: number
  err_msg: string
  payload: {
    data: T[]
    tag_list?: any[]
    default_account_id?: string
    default_group_name?: string
    default_remark?: string
    role_ids?: number[]
  }
}

/**
 * Axios响应结构
 */
interface AxiosApiResponse<T> {
  data: ApiResponse<T>
}

/**
 * 支持简繁转换的群组搜索
 * @param searchParams - 搜索参数
 * @returns Promise<ApiResponse<TgGroup>>
 */
export async function searchGroupsWithVariants(searchParams: TgGroupListParams): Promise<ApiResponse<TgGroup>> {
  const { group_name, ...otherParams } = searchParams

  // 如果没有群组名称搜索或不包含中文，直接调用原API
  if (!group_name || !containsChinese(group_name)) {
    const response = await tgGroupsApi.getList(searchParams)
    return response.data
  }

  // 获取简繁变体
  const variants = getSearchVariants(group_name)

  if (variants.length === 1) {
    // 没有变体，直接搜索
    const response = await tgGroupsApi.getList(searchParams)
    return response.data
  }

  console.log(`[简繁搜索] 关键词: "${group_name}", 搜索变体:`, variants)

  try {
    // 并发搜索所有变体
    const searchPromises = variants.map(async (variant) => {
      try {
        const response = await tgGroupsApi.getList({
          ...otherParams,
          group_name: variant
        })
        const result = response.data
        console.log(`[简繁搜索] 变体 "${variant}" 搜索结果:`, result.payload?.data?.length || 0, '条')
        return result
      } catch (error) {
        console.error(`[简繁搜索] 搜索变体 "${variant}" 失败:`, error)
        return {
          err_code: 1,
          err_msg: 'Search failed',
          payload: { data: [] }
        }
      }
    })

    const results = await Promise.all(searchPromises)

    // 合并结果并去重
    const groupMap = new Map<number, TgGroup>()
    let hasSuccessResult = false

    results.forEach(result => {
      if (result.err_code === 0 && result.payload?.data) {
        hasSuccessResult = true
        result.payload.data.forEach(group => {
          groupMap.set(group.id, group)
        })
      }
    })

    // 如果所有搜索都失败，返回错误
    if (!hasSuccessResult) {
      throw new Error('所有变体搜索都失败')
    }

    const mergedData = Array.from(groupMap.values())

    // 按最新消息时间排序（如果有的话）
    mergedData.sort((a, b) => {
      if (!a.latest_postal_time && !b.latest_postal_time) return 0
      if (!a.latest_postal_time) return 1
      if (!b.latest_postal_time) return -1
      return b.latest_postal_time.localeCompare(a.latest_postal_time)
    })

    console.log(`[简繁搜索] 合并后结果: ${mergedData.length} 条，去重完成`)

    // 获取第一个成功结果的额外信息（标签列表等）
    let additionalPayload = {}
    const firstSuccessResult = results.find(r => r.err_code === 0)
    if (firstSuccessResult && firstSuccessResult.payload) {
      const { data, ...rest } = firstSuccessResult.payload
      additionalPayload = rest
    }

    return {
      err_code: 0,
      err_msg: '',
      payload: {
        data: mergedData,
        ...additionalPayload
      }
    }

  } catch (error) {
    console.error('[简繁搜索] 搜索失败，降级到普通搜索:', error)
    // 降级到普通搜索
    try {
      const response = await tgGroupsApi.getList(searchParams)
      return response.data
    } catch (fallbackError) {
      console.error('[简繁搜索] 降级搜索也失败:', fallbackError)
      return {
        err_code: 1,
        err_msg: '搜索失败',
        payload: {
          data: []
        }
      }
    }
  }
}

/**
 * 获取搜索统计信息
 * @param originalKeyword - 原始关键词
 * @param mergedResults - 合并后的结果
 * @returns 搜索统计文本
 */
export function getSearchStats(originalKeyword: string, mergedResults: TgGroup[]): string {
  if (!originalKeyword || !containsChinese(originalKeyword)) {
    return `搜索完成，找到 ${mergedResults.length} 个结果`
  }

  const variants = getSearchVariants(originalKeyword)
  if (variants.length <= 1) {
    return `搜索完成，找到 ${mergedResults.length} 个结果`
  }

  return `简繁体搜索完成！搜索了: ${variants.join('、')}，共找到 ${mergedResults.length} 个结果`
}

/**
 * 检查是否应该使用简繁搜索
 * @param keyword - 搜索关键词
 * @returns boolean
 */
export function shouldUseVariantSearch(keyword?: string): boolean {
  if (!keyword) return false
  return containsChinese(keyword) && getSearchVariants(keyword).length > 1
}

export default {
  searchGroupsWithVariants,
  getSearchStats,
  shouldUseVariantSearch
}