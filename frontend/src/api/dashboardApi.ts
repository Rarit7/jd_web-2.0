/**
 * Dashboard 大屏展示 API 服务
 * 聚合 ad-analysis 的各类数据，一次性获取所有需要的数据
 */
import {
  apiGetTransactionMethods,
  apiGetDarkKeywordsAnalysis,
  apiGetDarkKeywordsWordCloud,
  apiGetPriceTrend,
  apiGetGeoHeatmap
} from './adAnalysis'
import type {
  TransactionMethodData,
  PriceTrendResponse,
  GeoHeatmapResponse
} from '@/types/adAnalysis'

/**
 * Dashboard 数据聚合响应类型
 */
export interface DashboardDataResponse {
  /** 交易方式分布数据 */
  transactionMethods: TransactionMethodData[] | null
  /** 黑词分析数据（词云格式：关键词+词频） */
  darkKeywords: Array<{ name: string; value: number }> | null
  /** 黑词趋势数据 */
  darkKeywordsTrend: { months: string[]; data: Record<string, number[]> } | null
  /** 价格趋势数据 */
  priceTrend: PriceTrendResponse | null
  /** 地理热力图数据 */
  geoHeatmap: GeoHeatmapResponse | null
  /** 各模块的错误信息 */
  errors: {
    transactionMethods: Error | null
    darkKeywords: Error | null
    priceTrend: Error | null
    geoHeatmap: Error | null
  }
}

/**
 * Dashboard 查询参数
 */
export interface DashboardQueryParams {
  /** 群组ID（可选，不提供时统计全表） */
  chat_id?: number
  /** 统计天数（默认365天） */
  days?: number
}

/**
 * 获取 Dashboard 大屏所需的所有数据
 *
 * 并行请求所有分析模块的 API，一次性返回所有数据
 *
 * @param params - 查询参数
 * @returns Promise<DashboardDataResponse>
 *
 * @example
 * ```typescript
 * const data = await fetchDashboardData({ days: 30 })
 * console.log(data.transactionMethods) // 交易方式数据
 * console.log(data.darkKeywords) // 黑词数据
 * ```
 */
export async function fetchDashboardData(
  params: DashboardQueryParams = {}
): Promise<DashboardDataResponse> {
  const queryParams = {
    chat_id: params.chat_id,
    days: params.days || 365
  }

  console.log('[DashboardApi] 开始获取 Dashboard 数据，参数:', queryParams)

  try {
    // 并行请求所有数据
    const results = await Promise.allSettled([
      apiGetTransactionMethods(queryParams),
      apiGetDarkKeywordsAnalysis(queryParams),
      apiGetDarkKeywordsWordCloud(queryParams),
      apiGetPriceTrend(queryParams),
      apiGetGeoHeatmap(queryParams)
    ])

    const [transactionResult, darkKeywordsResult, wordCloudResult, priceResult, geoResult] = results

    // 处理交易方式数据
    let transactionMethods: TransactionMethodData[] | null = null
    let transactionError: Error | null = null
    if (transactionResult.status === 'fulfilled') {
      transactionMethods = transactionResult.value.payload?.bar || null
      console.log('[DashboardApi] 交易方式数据加载成功:', transactionMethods?.length || 0, '条')
    } else {
      transactionError = transactionResult.reason
      console.error('[DashboardApi] 交易方式数据加载失败:', transactionError)
    }

    // 处理黑词数据（使用专用词云 API 获取所有关键词）
    let darkKeywords: Array<{ name: string; value: number }> | null = null
    let darkKeywordsTrend: { months: string[]; data: Record<string, number[]> } | null = null
    let darkKeywordsError: Error | null = null

    // 从 darkKeywordsResult 获取趋势数据
    if (darkKeywordsResult.status === 'fulfilled') {
      const payload = darkKeywordsResult.value.payload

      // 提取趋势数据（line 字段）
      if (payload?.line && payload.line.months && payload.line.data) {
        darkKeywordsTrend = {
          months: payload.line.months,
          data: payload.line.data
        }
        console.log('[DashboardApi] 黑词趋势数据加载成功')
      }
    } else {
      darkKeywordsError = darkKeywordsResult.reason
      console.error('[DashboardApi] 黑词趋势数据加载失败:', darkKeywordsError)
    }

    // 从 wordCloudResult 获取词云数据（包含所有触发过的关键词）
    if (wordCloudResult.status === 'fulfilled') {
      const wordCloudPayload = wordCloudResult.value.payload
      // 词云 API 直接返回所有关键词，取前 50 个用于展示
      darkKeywords = (Array.isArray(wordCloudPayload) ? wordCloudPayload : []).slice(0, 50)
      console.log('[DashboardApi] 词云数据加载成功:', darkKeywords.length, '个关键词（总共', wordCloudPayload?.length || 0, '个）')
    } else {
      console.warn('[DashboardApi] 词云数据加载失败，将使用空数组:', wordCloudResult.reason)
      darkKeywords = []
    }

    // 处理价格趋势数据
    let priceTrend: PriceTrendResponse | null = null
    let priceError: Error | null = null
    if (priceResult.status === 'fulfilled') {
      const payload = priceResult.value.payload
      if (payload && Array.isArray(payload.months) && typeof payload.data === 'object') {
        // 显式构造 PriceTrendResponse，使用 unknown 作为中间类型
        const trendData: PriceTrendResponse = {
          months: payload.months,
          data: payload.data as unknown as Record<string, number[]>
        }
        priceTrend = trendData
        console.log('[DashboardApi] 价格趋势数据加载成功')
      } else {
        console.warn('[DashboardApi] 价格趋势数据格式不正确')
      }
    } else {
      priceError = priceResult.reason
      console.error('[DashboardApi] 价格趋势数据加载失败:', priceError)
    }

    // 处理地理热力数据
    let geoHeatmap: GeoHeatmapResponse | null = null
    let geoError: Error | null = null
    if (geoResult.status === 'fulfilled') {
      const payload = geoResult.value.payload
      if (payload && Array.isArray(payload.provinces)) {
        // 确保 all_cities 字段存在
        const heatmapData: GeoHeatmapResponse = {
          provinces: payload.provinces,
          shandong_cities: payload.shandong_cities || [],
          all_cities: payload.all_cities || []
        }
        geoHeatmap = heatmapData
        console.log('[DashboardApi] 地理热力数据加载成功')
      } else {
        console.warn('[DashboardApi] 地理热力数据格式不正确')
      }
    } else {
      geoError = geoResult.reason
      console.error('[DashboardApi] 地理热力数据加载失败:', geoError)
    }

    return {
      transactionMethods,
      darkKeywords,
      darkKeywordsTrend,
      priceTrend,
      geoHeatmap,
      errors: {
        transactionMethods: transactionError,
        darkKeywords: darkKeywordsError,
        priceTrend: priceError,
        geoHeatmap: geoError
      }
    }

  } catch (error) {
    console.error('[DashboardApi] Dashboard 数据获取失败:', error)
    throw error
  }
}

/**
 * 刷新 Dashboard 缓存
 *
 * 调用后端清除缓存 API，确保下次获取最新数据
 *
 * @param chatId - 群组ID（可选）
 * @returns Promise<void>
 */
export async function refreshDashboardCache(chatId?: number): Promise<void> {
  try {
    // 这里可以调用清除缓存的 API
    // 如果 adAnalysis.ts 中有 apiClearAnalysisCache，可以直接使用
    console.log('[DashboardApi] 刷新 Dashboard 缓存, chatId:', chatId)
    // TODO: 实现缓存刷新逻辑
  } catch (error) {
    console.error('[DashboardApi] 缓存刷新失败:', error)
    throw error
  }
}

/**
 * 获取 Dashboard 数据统计摘要
 *
 * 返回各类数据的统计摘要信息，用于显示在大屏顶部
 *
 * @param params - 查询参数
 * @returns Promise<Object>
 */
export async function fetchDashboardSummary(
  params: DashboardQueryParams = {}
): Promise<{
  totalTransactions: number
  totalDarkKeywords: number
  totalPriceRecords: number
  totalGeoRecords: number
  lastUpdate: string
}> {
  try {
    const data = await fetchDashboardData(params)

    return {
      totalTransactions: data.transactionMethods?.reduce((sum, item) => sum + (item.value || 0), 0) || 0,
      totalDarkKeywords: data.darkKeywords?.reduce((sum, item) => sum + (item.value || 0), 0) || 0,
      totalPriceRecords: Object.values(data.priceTrend?.data || {}).reduce(
        (sum, values) => sum + (Array.isArray(values) ? values.length : 0), 0
      ),
      totalGeoRecords: data.geoHeatmap?.provinces?.reduce((sum, item) => sum + (item.value || 0), 0) || 0,
      lastUpdate: new Date().toISOString()
    }
  } catch (error) {
    console.error('[DashboardApi] 获取统计摘要失败:', error)
    return {
      totalTransactions: 0,
      totalDarkKeywords: 0,
      totalPriceRecords: 0,
      totalGeoRecords: 0,
      lastUpdate: new Date().toISOString()
    }
  }
}

export default {
  fetchDashboardData,
  refreshDashboardCache,
  fetchDashboardSummary
}
