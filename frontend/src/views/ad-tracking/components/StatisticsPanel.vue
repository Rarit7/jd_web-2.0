<template>
  <div class="statistics-panel">
    <!-- 总体统计卡片 - 始终保持一行 -->
    <el-row :gutter="16" class="stats-cards">
      <el-col :span="4">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon total-icon">
              <el-icon :size="28"><Document /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">广告记录总数</div>
              <div class="stat-value">{{ formatNumber(stats?.summary.total_records || 0) }}</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="4">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon occurrence-icon">
              <el-icon :size="28"><PieChart /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">累计出现次数</div>
              <div class="stat-value">{{ formatNumber(stats?.summary.total_occurrences || 0) }}</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="4">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon user-icon">
              <el-icon :size="28"><User /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">涉及用户数</div>
              <div class="stat-value">{{ formatNumber(stats?.summary.unique_users || 0) }}</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="4">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon chat-icon">
              <el-icon :size="28"><ChatDotRound /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">涉及群组数</div>
              <div class="stat-value">{{ formatNumber(stats?.summary.unique_chats || 0) }}</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="4">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon merchant-icon">
              <el-icon :size="28"><Shop /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">商家数量</div>
              <div class="stat-value">{{ formatNumber(stats?.summary.unique_merchants || 0) }}</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 预留一个空列，总共6列平分 -->
      <el-col :span="4">
        <el-card shadow="hover" class="stat-card placeholder-card" style="visibility: hidden;">
          <div class="stat-content">
            <div class="stat-icon">
              <el-icon :size="28"><Document /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">占位</div>
              <div class="stat-value">0</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 图表区域 - 自适应布局 -->
    <el-row :gutter="16" class="charts-row">
      <!-- 内容类型分布 -->
      <el-col :xs="24" :sm="24" :md="12" :lg="8" :xl="8">
        <el-card shadow="hover" class="chart-card">
          <template #header>
            <div class="chart-header">
              <span class="chart-title">内容类型分布</span>
            </div>
          </template>
          <div ref="contentTypeChartRef" class="chart"></div>
        </el-card>
      </el-col>

      <!-- Top用户排行 -->
      <el-col :xs="24" :sm="24" :md="12" :lg="8" :xl="8">
        <el-card shadow="hover" class="chart-card">
          <template #header>
            <div class="chart-header">
              <span class="chart-title">Top 10 活跃推广者</span>
            </div>
          </template>
          <div ref="topUsersChartRef" class="chart"></div>
        </el-card>
      </el-col>

      <!-- Top商家排行 -->
      <el-col :xs="24" :sm="24" :md="12" :lg="8" :xl="8">
        <el-card shadow="hover" class="chart-card">
          <template #header>
            <div class="chart-header">
              <span class="chart-title">Top 10 活跃商家</span>
            </div>
          </template>
          <div ref="topMerchantsChartRef" class="chart"></div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import echarts from '@/utils/echarts'
import { Document, PieChart as PieChartIcon, User, ChatDotRound, Shop } from '@element-plus/icons-vue'
import type { StatsResponse } from '@/types/adTracking'
import type { ECharts } from 'echarts/core'

// Chart 实例
let contentTypeChart: ECharts | null = null
let topUsersChart: ECharts | null = null
let topMerchantsChart: ECharts | null = null

// Chart DOM 引用
const contentTypeChartRef = ref<HTMLElement>()
const topUsersChartRef = ref<HTMLElement>()
const topMerchantsChartRef = ref<HTMLElement>()

interface Props {
  stats: StatsResponse | null
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  loading: false
})

// ==================== 内容类型映射 ====================

const contentTypeLabels: Record<string, string> = {
  url: 'URL链接',
  telegram_account: '@账户',
  t_me_invite: 't.me邀请',
  t_me_channel_msg: 't.me频道消息',
  t_me_private_invite: 't.me私聊邀请',
  telegraph: 'Telegraph'
}

// ==================== 工具函数 ====================

const formatNumber = (num: number): string => {
  return num.toLocaleString('zh-CN')
}

// ==================== 图表配置 ====================

// 内容类型饼图
const contentTypeChartOption = computed(() => {
  if (!props.stats?.content_type_stats) return {}

  const data = props.stats.content_type_stats.map((item) => ({
    name: contentTypeLabels[item.content_type] || item.content_type,
    value: item.count
  }))

  return {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)'
    },
    legend: {
      orient: 'vertical',
      right: 10,
      top: 'center',
      textStyle: {
        fontSize: 12
      }
    },
    series: [
      {
        name: '内容类型',
        type: 'pie',
        radius: ['40%', '70%'],
        center: ['40%', '50%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: {
          show: false
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 14,
            fontWeight: 'bold'
          }
        },
        data: data,
        color: ['#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de', '#3ba272']
      }
    ]
  }
})

// Top用户柱状图
const topUsersChartOption = computed(() => {
  if (!props.stats?.top_users) return {}

  const users = props.stats.top_users.slice(0, 10)
  const names = users.map((u) => u.nickname || u.user_id.slice(0, 10))
  const values = users.map((u) => u.count)

  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'value',
      boundaryGap: [0, 0.01]
    },
    yAxis: {
      type: 'category',
      data: names,
      axisLabel: {
        fontSize: 11,
        interval: 0
      }
    },
    series: [
      {
        name: '推广次数',
        type: 'bar',
        data: values,
        itemStyle: {
          color: '#5470c6',
          borderRadius: [0, 4, 4, 0]
        },
        label: {
          show: true,
          position: 'right',
          fontSize: 11
        }
      }
    ]
  }
})

// Top商家漏斗图
const topMerchantsChartOption = computed(() => {
  if (!props.stats?.top_merchants) return {}

  const merchants = props.stats.top_merchants.slice(0, 10)
  const data = merchants.map((m) => ({
    name: m.merchant_name,
    value: m.total_occurrences,
    count: m.count
  }))

  return {
    tooltip: {
      trigger: 'item',
      formatter: (params: any) => {
        const merchant = merchants[params.dataIndex]
        return `${params.name}<br/>广告出现: ${merchant.total_occurrences} 次<br/>记录数: ${merchant.count}`
      }
    },
    series: [
      {
        name: '商家活跃度',
        type: 'funnel',
        left: '10%',
        top: 20,
        bottom: 20,
        width: '80%',
        min: 0,
        max: data[0]?.value || 100,
        minSize: '0%',
        maxSize: '100%',
        sort: 'descending',
        gap: 2,
        label: {
          show: true,
          position: 'inside',
          formatter: '{b}: {c}',
          fontSize: 11,
          color: '#333'
        },
        labelLine: {
          show: false
        },
        itemStyle: {
          borderColor: '#fff',
          borderWidth: 1
        },
        emphasis: {
          label: {
            fontSize: 13,
            fontWeight: 'bold',
            color: '#000'
          }
        },
        data: data,
        color: ['#5470c6', '#73c0de', '#91cc75', '#fac858', '#ee6666', '#9a60b4', '#3ba272', '#fc8452', '#ea7ccc', '#5ad8a6']
      }
    ]
  }
})

// 初始化图表
function initCharts() {
  if (contentTypeChartRef.value && !contentTypeChart) {
    contentTypeChart = echarts.init(contentTypeChartRef.value)
  }
  if (topUsersChartRef.value && !topUsersChart) {
    topUsersChart = echarts.init(topUsersChartRef.value)
  }
  if (topMerchantsChartRef.value && !topMerchantsChart) {
    topMerchantsChart = echarts.init(topMerchantsChartRef.value)
  }
}

// 更新图表
function updateCharts() {
  if (contentTypeChart && contentTypeChartOption.value) {
    contentTypeChart.setOption(contentTypeChartOption.value)
  }
  if (topUsersChart && topUsersChartOption.value) {
    topUsersChart.setOption(topUsersChartOption.value)
  }
  if (topMerchantsChart && topMerchantsChartOption.value) {
    topMerchantsChart.setOption(topMerchantsChartOption.value)
  }
}

// 窗口大小调整
function handleResize() {
  contentTypeChart?.resize()
  topUsersChart?.resize()
  topMerchantsChart?.resize()
}

// 监听数据变化
watch(() => props.stats, () => {
  updateCharts()
}, { deep: true })

// 生命周期
onMounted(() => {
  initCharts()
  updateCharts()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  contentTypeChart?.dispose()
  topUsersChart?.dispose()
  topMerchantsChart?.dispose()
  contentTypeChart = null
  topUsersChart = null
  topMerchantsChart = null
})
</script>

<style scoped lang="scss">
.statistics-panel {
  width: 100%;

  .stats-cards {
    margin-bottom: 16px;

    .stat-card {
      height: 100%;

      :deep(.el-card__body) {
        padding: 16px;
      }

      .stat-content {
        display: flex;
        align-items: center;
        gap: 12px;

        .stat-icon {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 48px;
          height: 48px;
          border-radius: 10px;
          flex-shrink: 0;

          &.total-icon {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #fff;
          }

          &.occurrence-icon {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: #fff;
          }

          &.user-icon {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            color: #fff;
          }

          &.chat-icon {
            background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
            color: #fff;
          }

          &.merchant-icon {
            background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
            color: #fff;
          }
        }

        .stat-info {
          flex: 1;
          min-width: 0;

          .stat-label {
            font-size: 12px;
            color: #909399;
            margin-bottom: 2px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
          }

          .stat-value {
            font-size: 20px;
            font-weight: 600;
            color: #303133;
            line-height: 1.2;
          }
        }
      }
    }
  }

  .charts-row {
    .chart-card {
      margin-bottom: 16px;

      :deep(.el-card__body) {
        padding: 16px;
      }

      .chart-header {
        display: flex;
        align-items: center;
        justify-content: space-between;

        .chart-title {
          font-weight: 600;
          font-size: 14px;
          color: #303133;
        }
      }

      .chart {
        width: 100%;
        height: 280px;
      }
    }
  }
}

// 响应式调整
@media (max-width: 768px) {
  .statistics-panel {
    .stats-cards {
      .stat-card {
        :deep(.el-card__body) {
          padding: 15px;
        }

        .stat-content {
          gap: 12px;

          .stat-icon {
            width: 48px;
            height: 48px;

            .el-icon {
              font-size: 24px !important;
            }
          }

          .stat-info {
            .stat-label {
              font-size: 12px;
            }

            .stat-value {
              font-size: 20px;
            }
          }
        }
      }
    }

    .charts-row {
      .chart-card {
        .chart {
          height: 250px;
        }
      }
    }
  }
}
</style>
