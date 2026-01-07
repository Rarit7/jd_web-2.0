<template>
  <div class="word-cloud-chart" v-loading="loading">
    <div ref="chartRef" class="chart-container"></div>
    <div v-if="!data || data.length === 0" class="empty-state">
      <p>暂无数据</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, onUnmounted } from 'vue'
import echarts from '@/utils/echarts'
import 'echarts-wordcloud'

interface WordCloudData {
  name: string
  value: number
}

interface Props {
  data?: WordCloudData[]
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  data: () => [],
  loading: false
})

const chartRef = ref()
let chartInstance: any = null

// 词云颜色配置
const colors = [
  '#4c60ff', '#27d08a', '#2db7f5', '#f50', '#fa541c',
  '#faad14', '#722ed1', '#eb2f96', '#13c2c2', '#52c41a'
]

function initChart() {
  if (!chartRef.value) return

  chartInstance = echarts.init(chartRef.value)
  updateChart()
}

function updateChart() {
  if (!chartInstance || !props.data || props.data.length === 0) return

  const option = {
    backgroundColor: 'transparent',
    tooltip: {
      show: true,
      formatter: (params: any) => `${params.name}: ${params.value}次`
    },
    series: [{
      type: 'wordCloud',
      gridSize: 4,
      sizeRange: [14, 60],
      rotationRange: [0, 0],
      shape: 'circle',
      width: '100%',
      height: '100%',
      drawOutOfBound: false,
      textStyle: {
        fontFamily: 'Arial, "Microsoft YaHei", sans-serif',
        fontWeight: 'bold',
        color: () => colors[Math.floor(Math.random() * colors.length)]
      },
      emphasis: {
        focus: 'self',
        textStyle: {
          shadowBlur: 10,
          shadowColor: '#333'
        }
      },
      data: props.data.map(item => ({
        name: item.name,
        value: item.value
      }))
    }]
  }

  chartInstance.setOption(option, true)
}

function resize() {
  if (chartInstance) {
    chartInstance.resize()
  }
}

// 监听数据变化
watch(
  () => props.data,
  () => {
    updateChart()
  },
  { deep: true }
)

// 监听加载状态
watch(
  () => props.loading,
  (newVal) => {
    if (!newVal && props.data && props.data.length > 0) {
      updateChart()
    }
  }
)

onMounted(() => {
  initChart()
  window.addEventListener('resize', resize)
})

onUnmounted(() => {
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
  window.removeEventListener('resize', resize)
})

defineExpose({
  resize
})
</script>

<style scoped lang="scss">
.word-cloud-chart {
  width: 100%;
  height: 100%;
  min-height: 400px;
  position: relative;

  .chart-container {
    width: 100%;
    height: 100%;
    min-height: 400px;
  }

  .empty-state {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    text-align: center;
    color: #909399;
    font-size: 14px;
  }
}
</style>
