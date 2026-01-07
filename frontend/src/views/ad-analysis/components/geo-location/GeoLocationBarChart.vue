<template>
  <div class="bar-chart-container">
    <div ref="chartRef" class="bar-chart"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts'
import type { ECharts, EChartsOption } from 'echarts'
import { initEChartsSafely, setupVisibilityObserver } from '@/utils/echarts-helper'
import type { GeoLocationData } from '@/types/adAnalysis'

interface Props {
  data: GeoLocationData[] | null
  loading: boolean
}

const props = defineProps<Props>()

const chartRef = ref<HTMLElement | null>(null)
let chart: ECharts | null = null

onMounted(async () => {
  // 使用安全初始化函数，处理标签页隐藏时 DOM 宽高为 0 的问题
  chart = await initEChartsSafely(chartRef.value)

  // 如果初始化成功，更新图表
  if (chart) {
    updateChart()
  }

  // 响应窗口resize
  const handleResize = () => {
    chart?.resize()
  }
  window.addEventListener('resize', handleResize)

  // 监听容器可见性
  const unobserve = setupVisibilityObserver(
    chartRef.value,
    chart,
    // 延迟初始化回调：如果初始化失败，等到标签页可见时再初始化
    async () => {
      if (!chart && chartRef.value) {
        chart = await initEChartsSafely(chartRef.value)
        if (chart) {
          updateChart()
        }
      }
    }
  )

  // 保存清理函数
  if (chart) {
    chart._dispose = () => {
      unobserve()
      window.removeEventListener('resize', handleResize)
    }
  }
})

function updateChart() {
  // 如果图表未初始化，不更新
  if (!chart) return

  if (!props.data || props.data.length === 0) {
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

  // 水平柱状图，按排名显示（后端可能返回 count 或 value）
  const sortedData = [...props.data].slice(0, 50).sort((a, b) => (b.count || 0) - (a.count || 0))

  const option: EChartsOption = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'value',
      name: '热度'
    },
    yAxis: {
      type: 'category',
      data: sortedData.map(item => item.province + (item.city ? `-${item.city}` : '')),
      inverse: true  // 反转轴，让最大值显示在顶部
    },
    series: [
      {
        data: sortedData.map(item => item.count || 0),
        type: 'bar',
        barWidth: '60%',
        itemStyle: {
          color: new (echarts as any).graphic.LinearGradient(1, 0, 0, 0, [
            { offset: 0, color: '#83bff6' },
            { offset: 0.5, color: '#188df0' },
            { offset: 1, color: '#188df0' }
          ])
        }
      }
    ]
  }

  chart.setOption(option)
}

// 监听数据变化
watch(() => props.data, () => {
  updateChart()
}, { deep: true })

// 监听loading状态
watch(() => props.loading, (val) => {
  if (chart) {
    if (val) {
      chart.showLoading('default')
    } else {
      chart.hideLoading()
    }
  }
})

onBeforeUnmount(() => {
  if (chart) {
    if (typeof chart._dispose === 'function') {
      chart._dispose()
    }
    chart.dispose()
  }
  chart = null
})
</script>

<style scoped lang="scss">
.bar-chart-container {
  width: 100%;
  height: 500px;

  .bar-chart {
    width: 100%;
    height: 100%;
  }
}
</style>
