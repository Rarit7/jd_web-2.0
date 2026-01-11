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

// 词云颜色配置 - 专业渐变色配置
const colors = [
  // 蓝色系
  '#4c60ff', '#5a7aff', '#1890ff', '#0050b3', '#0037a6',
  // 绿色系
  '#27d08a', '#52c41a', '#13c2c2', '#1890ff', '#52a836',
  // 紫色系
  '#722ed1', '#b37feb', '#9254de', '#d946ef', '#a855f7',
  // 红色/橙色系
  '#fa541c', '#f5222d', '#ff4d4f', '#ff7a45', '#ffa940',
  // 黄色系
  '#faad14', '#ffc53d', '#fadb14', '#eac855',
  // 粉色系
  '#eb2f96', '#f759ab', '#ff1493', '#ff69b4',
  // 青色系
  '#13c2c2', '#36cfc9', '#5cdbd3', '#87e8de'
]

function initChart() {
  if (!chartRef.value) return

  chartInstance = echarts.init(chartRef.value)
  updateChart()
}

function updateChart() {
  if (!chartInstance || !props.data || props.data.length === 0) return

  // 计算最大最小值用于字体大小映射
  const values = props.data.map(item => item.value)
  const maxValue = Math.max(...values)
  const minValue = Math.min(...values)

  const option = {
    backgroundColor: 'transparent',
    tooltip: {
      show: true,
      backgroundColor: 'rgba(0, 0, 0, 0.8)',
      borderColor: '#4c60ff',
      textStyle: {
        color: '#fff',
        fontSize: 12
      },
      formatter: (params: any) => {
        const percentage = ((params.value / maxValue) * 100).toFixed(1)
        return `<strong>${params.name}</strong><br/>触发频率: ${params.value}次<br/>占比: ${percentage}%`
      }
    },
    series: [{
      type: 'wordCloud',
      gridSize: 3,
      sizeRange: [16, 72],
      rotationRange: [0, 0],
      shape: 'circle',
      width: '100%',
      height: '100%',
      drawOutOfBound: false,
      textStyle: {
        fontFamily: 'Arial, "Microsoft YaHei", "PingFang SC", sans-serif',
        fontWeight: 'bold',
        color: () => colors[Math.floor(Math.random() * colors.length)]
      },
      emphasis: {
        focus: 'self',
        textStyle: {
          shadowBlur: 15,
          shadowColor: 'rgba(76, 96, 255, 0.5)',
          shadowOffsetX: 0,
          shadowOffsetY: 0
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
