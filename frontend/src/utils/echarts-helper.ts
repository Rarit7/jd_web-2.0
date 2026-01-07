/**
 * ECharts 初始化辅助工具
 * 用于处理标签页隐藏时 DOM 宽高为 0 的问题
 */
import * as echarts from 'echarts'
import type { ECharts } from 'echarts'
import { nextTick } from 'vue'

/**
 * 安全初始化 ECharts 实例
 *
 * 解决问题：当图表在隐藏标签页中初始化时，DOM 宽高为 0 导致的警告
 *
 * @param container - 图表容器 DOM 元素
 * @param retries - 重试次数（默认10次）
 * @param retryDelay - 重试间隔（默认100ms）
 * @returns ECharts 实例
 */
export async function initEChartsSafely(
  container: HTMLElement | null,
  retries: number = 10,
  retryDelay: number = 100
): Promise<ECharts | null> {
  if (!container) return null

  // 首先等待 DOM 完全渲染
  await nextTick()

  let chart: ECharts | null = null

  for (let i = 0; i < retries; i++) {
    try {
      // 检查容器宽高
      const width = container.clientWidth
      const height = container.clientHeight

      if (width > 0 && height > 0) {
        // 容器有正确的尺寸，初始化图表
        chart = echarts.init(container, null, {
          useDirtyRect: true,
          useCoarsePointer: false
        })
        console.debug(`[ECharts] 初始化成功 (尝试 ${i + 1}/${retries})，容器尺寸: ${width}x${height}`)
        return chart
      } else {
        if (i === 0 || i % 3 === 0) {
          console.debug(`[ECharts] 容器尺寸: ${width}x${height}，等待重试 (${i + 1}/${retries})...`)
        }
      }
    } catch (error) {
      console.error(`[ECharts] 初始化失败 (尝试 ${i + 1}/${retries}):`, error)
    }

    // 如果不是最后一次尝试，等待后重试
    if (i < retries - 1) {
      await new Promise(resolve => setTimeout(resolve, retryDelay))
    }
  }

  // 所有重试都失败，返回null
  // 容器尺寸为0（标签页隐藏），不应该强制初始化
  // 应该等待容器变为可见（setupVisibilityObserver）或数据加载完成
  console.debug('[ECharts] 容器尺寸仍为 0，暂不初始化。等待容器可见或数据加载完成时再初始化')
  return null
}

/**
 * 在 watch 数据变化时安全更新图表
 * 如果图表未初始化或已销毁，自动初始化
 */
export function updateChartSafely(
  chart: ECharts | null,
  container: HTMLElement | null,
  callback: (chart: ECharts) => void
): void {
  if (chart && !chart.isDisposed?.()) {
    // 图表已初始化且未销毁
    callback(chart)
  } else if (container) {
    // 图表未初始化，尝试初始化并更新
    initEChartsSafely(container).then((newChart) => {
      if (newChart) {
        callback(newChart)
      }
    })
  }
}

/**
 * 监听图表容器可见性变化
 * 当标签页切换时重新调整图表大小
 * 如果图表未初始化，则在可见时进行初始化
 */
export function setupVisibilityObserver(
  container: HTMLElement | null,
  chart: ECharts | null,
  initCallback?: () => Promise<void>
): () => void {
  if (!container) return () => {}

  let isInitializing = false

  // 使用 IntersectionObserver 监听容器可见性
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          // 容器变为可见
          console.debug('[ECharts] IntersectionObserver: 容器变为可见')
          if (chart && !chart.isDisposed?.()) {
            // 如果图表已初始化且未销毁，调整大小以重新计算尺寸
            console.debug('[ECharts] 图表已初始化，调用 resize() 重新计算尺寸')
            setTimeout(() => {
              if (chart && !chart.isDisposed?.()) {
                chart.resize()
                console.debug('[ECharts] resize() 调用完成')
              }
            }, 0)
          } else if (initCallback && !isInitializing) {
            // 如果图表未初始化，执行初始化回调（防止多次初始化）
            isInitializing = true
            console.debug('[ECharts] 图表未初始化，执行初始化回调')
            initCallback()
              .then(() => {
                console.debug('[ECharts] 初始化回调执行成功')
              })
              .catch((error) => {
                console.error('[ECharts] 初始化回调执行失败:', error)
              })
              .finally(() => {
                isInitializing = false
              })
          }
        }
      })
    },
    { threshold: 0.1 }
  )

  observer.observe(container)

  // 返回取消观察的函数
  return () => observer.disconnect()
}

export default {
  initEChartsSafely,
  updateChartSafely,
  setupVisibilityObserver
}
