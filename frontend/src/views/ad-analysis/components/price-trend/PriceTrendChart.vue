<template>
  <div class="chart-container">
    <div ref="chartRef" class="chart"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, onBeforeUnmount, nextTick } from 'vue'
import type { ECharts, EChartsOption } from 'echarts'
import { initEChartsSafely, setupVisibilityObserver } from '@/utils/echarts-helper'
import type { PriceTrendData } from '@/types/adAnalysis'

interface Props {
  data: PriceTrendData | null
  loading: boolean
  visible?: boolean
}

const props = defineProps<Props>()

const chartRef = ref<HTMLElement | null>(null)
let chart: ECharts | null = null
let isInitializing = false

let unobserve: (() => void) | null = null
let handleResize: (() => void) | null = null

/**
 * 初始化图表实例
 */
async function initChart(): Promise<boolean> {
  if (chart && !chart.isDisposed?.()) {
    // 图表已初始化且未销毁
    return true
  }

  if (isInitializing || !chartRef.value) {
    return false
  }

  isInitializing = true
  try {
    console.debug('[PriceTrendChart] 开始初始化图表...')
    chart = await initEChartsSafely(chartRef.value)
    if (chart) {
      console.debug('[PriceTrendChart] 图表初始化成功')
      return true
    } else {
      console.debug('[PriceTrendChart] 容器尺寸为0或初始化失败，待后续重试')
      return false
    }
  } catch (error) {
    console.error('[PriceTrendChart] 初始化图表异常:', error)
    return false
  } finally {
    isInitializing = false
  }
}

onMounted(async () => {
  console.debug('[PriceTrendChart] 组件已mounted')

  // 响应窗口resize
  handleResize = () => {
    if (chart && !chart.isDisposed?.()) {
      chart.resize()
    }
  }
  window.addEventListener('resize', handleResize)

  // 监听容器可见性变化
  unobserve = setupVisibilityObserver(
    chartRef.value,
    chart,
    // 当容器变为可见时的回调 - 初始化或调整大小图表
    async () => {
      console.debug('[PriceTrendChart] 容器变为可见')

      const initialized = await initChart()
      if (initialized) {
        await updateChart()
      }
    }
  )
})

// 数据加载完成后更新图表
watch(() => props.data, async () => {
  console.debug('[PriceTrendChart] 检测到数据变化')
  const initialized = await initChart()
  if (initialized) {
    await updateChart()
  }
}, { deep: true, immediate: false })

// 当标签页变为可见时初始化图表
watch(() => props.visible, async (isVisible) => {
  if (isVisible) {
    console.debug('[PriceTrendChart] 标签页变为可见')
    const initialized = await initChart()
    if (initialized) {
      await nextTick()
      if (chart && !chart.isDisposed?.()) {
        chart.resize()
      }
      await updateChart()
    }
  }
})

async function updateChart() {
  try {
    // 确保图表已初始化
    const initialized = await initChart()
    if (!initialized) {
      console.debug('[PriceTrendChart] 图表初始化失败，暂不更新数据')
      return
    }

    if (!chart) {
      console.warn('[PriceTrendChart] 图表为null，无法更新')
      return
    }

    // 检查图表是否已销毁
    if (chart.isDisposed?.()) {
      console.warn('[PriceTrendChart] 图表已销毁，无法更新')
      chart = null
      return
    }

    // 检查数据
    if (!props.data || !props.data.months || !props.data.data || Object.keys(props.data.data).length === 0) {
      chart.setOption({
        title: {
          text: '暂无数据',
          left: 'center',
          top: 'center',
          textStyle: { color: '#909399' }
        }
      })
      return
    }

    const seriesData = Object.entries(props.data.data).map(([name, values]) => ({
      name,
      type: 'line' as const,
      data: values,
      smooth: true,
      symbolSize: 6,
      lineStyle: {
        width: 2
      }
    }))

    const option: EChartsOption = {
      title: {
        show: false
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'cross' }
      },
      legend: {
        data: Object.keys(props.data.data),
        top: 10,
        type: 'scroll'
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        top: '15%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: props.data.months,
        axisLabel: {
          interval: Math.floor(props.data.months.length / 12) || 0
        }
      },
      yAxis: {
        type: 'value',
        name: '价格'
      },
      series: seriesData
    }

    chart.setOption(option)
    console.debug('[PriceTrendChart] 数据更新成功')
  } catch (error) {
    console.error('[PriceTrendChart] 更新图表异常:', error)
  }
}

// 监听loading状态
watch(() => props.loading, (val) => {
  if (chart && !chart.isDisposed?.()) {
    if (val) {
      chart.showLoading('default')
    } else {
      chart.hideLoading()
    }
  }
})

onBeforeUnmount(() => {
  console.debug('[PriceTrendChart] 组件卸载')
  // 清理事件监听
  if (handleResize) {
    window.removeEventListener('resize', handleResize)
  }
  if (unobserve) {
    unobserve()
  }
  // 销毁图表
  if (chart && !chart.isDisposed?.()) {
    chart.dispose()
  }
  chart = null
})
</script>

<style scoped lang="scss">
.chart-container {
  width: 100%;
  height: 400px;

  .chart {
    width: 100%;
    height: 100%;
  }
}
</style>
