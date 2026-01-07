<template>
  <div class="pie-chart-container">
    <div ref="chartRef" class="pie-chart"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, onBeforeUnmount } from 'vue'
import type { ECharts, EChartsOption } from 'echarts'
import { initEChartsSafely, setupVisibilityObserver } from '@/utils/echarts-helper'
import type { DarkKeywordsPieData } from '@/types/adAnalysis'

interface Props {
  data: DarkKeywordsPieData[] | null
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

  const option: EChartsOption = {
    title: {
      show: false  // 清除"暂无数据"的title
    },
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)'
    },
    legend: {
      show: false
    },
    series: [
      {
        name: '黑词分布',
        type: 'pie',
        radius: ['40%', '70%'],
        data: props.data.map(item => ({
          value: item.value,
          name: item.name
        })),
        emphasis: {
          label: {
            show: true,
            fontSize: 16,
            fontWeight: 'bold'
          }
        },
        labelLine: {
          show: true
        },
        label: {
          show: true,
          formatter: '{b}: {d}%'
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
      chart.showLoading('default', {
        text: '加载中...',
        maskColor: 'rgba(255, 255, 255, 0.8)',
        textColor: '#000'
      })
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
.pie-chart-container {
  width: 100%;
  height: 400px;

  .pie-chart {
    width: 100%;
    height: 100%;
  }
}
</style>
