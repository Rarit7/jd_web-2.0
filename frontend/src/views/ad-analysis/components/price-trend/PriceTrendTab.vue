<template>
  <div class="price-trend-tab">
    <!-- 控制条 -->
    <div class="control-bar">
      <div class="left">
        <el-button type="primary" @click="handleSearch" :loading="loading">
          查询
        </el-button>
        <el-button @click="handleReset">
          重置
        </el-button>
      </div>

      <div class="right">
        <span style="margin-right: 10px">数据周期：</span>
        <el-select
          v-model="selectedDays"
          style="width: 150px"
          @change="handleSearch"
        >
          <el-option label="近30天" :value="30" />
          <el-option label="近90天" :value="90" />
          <el-option label="近180天" :value="180" />
          <el-option label="近365天" :value="365" />
        </el-select>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="statistics-cards" v-if="statistics">
      <div class="stat-card">
        <div class="stat-label">最高价格</div>
        <div class="stat-value">{{ statistics.max_price.toFixed(2) }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">最低价格</div>
        <div class="stat-value">{{ statistics.min_price.toFixed(2) }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">平均价格</div>
        <div class="stat-value">{{ statistics.avg_price.toFixed(2) }}</div>
      </div>
      <div class="stat-card" :class="{ positive: statistics.price_change > 0 }">
        <div class="stat-label">价格波动</div>
        <div class="stat-value">{{ statistics.price_change > 0 ? '+' : '' }}{{ statistics.price_change.toFixed(2) }}%</div>
      </div>
    </div>

    <!-- 标签页 -->
    <el-tabs v-model="activeTab" class="data-tabs">
      <!-- 价格趋势图 -->
      <el-tab-pane label="价格趋势" name="chart">
        <div v-loading="loading" style="padding: 20px">
          <div class="chart-box">
            <PriceTrendChart
              :data="chartData"
              :loading="loading"
              :visible="activeTab === 'chart'"
            />
          </div>
        </div>
      </el-tab-pane>

      <!-- 历史记录 -->
      <el-tab-pane label="历史记录" name="history">
        <div v-loading="loading" style="padding: 20px">
          <PriceHistoryTable
            :data="tableData"
            :loading="loading"
            :total="total"
            :page="currentPage"
            :page-size="pageSize"
            @page-change="handlePageChange"
          />
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import {
  usePriceTrendStore,
  useAdAnalysisStore
} from '@/store/modules/adAnalysis'
import {
  apiGetPriceTrend,
  apiGetPriceHistory
} from '@/api/adAnalysis'
import PriceTrendChart from './PriceTrendChart.vue'
import PriceHistoryTable from './PriceHistoryTable.vue'
import type {
  PriceTrendData,
  PriceHistoryRecord,
  PriceTrendStatistics
} from '@/types/adAnalysis'

// Stores
const priceTrendStore = usePriceTrendStore()
const analysisStore = useAdAnalysisStore()

// State
const loading = ref(false)
const activeTab = ref<'chart' | 'history'>('chart')
const chartData = ref<PriceTrendData | null>(null)
const statistics = ref<PriceTrendStatistics | null>(null)
const tableData = ref<PriceHistoryRecord[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const selectedDays = ref(365)

// Methods
async function loadData() {
  loading.value = true
  try {
    const params: any = {
      days: selectedDays.value
    }

    // 如果选了 chat_id，则添加到参数中；否则查询全表
    if (analysisStore.selectedChatId) {
      params.chat_id = analysisStore.selectedChatId
    }

    // 并行加载数据
    const [trendResponse, historyResponse] = await Promise.all([
      apiGetPriceTrend(params),
      apiGetPriceHistory({
        ...params,
        offset: (currentPage.value - 1) * pageSize.value,
        limit: pageSize.value
      })
    ])

    // 后端直接返回 {months, data}
    chartData.value = {
      months: trendResponse.payload.months || [],
      data: trendResponse.payload.data || {}
    }

    // 从价格数据计算统计信息（排除0值）
    const allPrices = Object.values(trendResponse.payload.data || {})
      .flat()
      .filter((v: any) => v > 0) as number[]

    if (allPrices.length > 0) {
      const maxPrice = Math.max(...allPrices)
      const minPrice = Math.min(...allPrices)
      const avgPrice = allPrices.reduce((a, b) => a + b, 0) / allPrices.length

      // 计算价格波动（从所有价格中取第一个非零值和最后一个非零值）
      const nonZeroPrices = allPrices.filter(p => p > 0)
      const firstPrice = nonZeroPrices[0] || 0
      const lastPrice = nonZeroPrices[nonZeroPrices.length - 1] || 0
      const priceChange = firstPrice ? ((lastPrice - firstPrice) / firstPrice * 100) : 0

      statistics.value = {
        max_price: maxPrice,
        min_price: minPrice,
        avg_price: avgPrice,
        price_change: priceChange
      }
    } else {
      statistics.value = {
        max_price: 0,
        min_price: 0,
        avg_price: 0,
        price_change: 0
      }
    }

    tableData.value = historyResponse.payload.data || []
    total.value = historyResponse.payload.total || 0

    priceTrendStore.setChartData(chartData.value)
    priceTrendStore.setStatistics(statistics.value)
    priceTrendStore.setHistoryData(tableData.value, total.value)
  } catch (error) {
    console.error('加载数据失败:', error)
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  currentPage.value = 1
  loadData()
}

function handleReset() {
  selectedDays.value = 365
  currentPage.value = 1
  priceTrendStore.reset()
  loadData()
}

function handlePageChange(page: number) {
  currentPage.value = page
  loadData()
}

// Lifecycle
onMounted(() => {
  // 页面加载时直接加载数据（可以是全表统计，也可以是特定 chat_id 的统计）
  loadData()
})

// Watch for store changes
watch(
  () => analysisStore.selectedChatId,
  () => {
    // 当 selectedChatId 改变时，重新加载数据
    loadData()
  }
)
</script>

<style scoped lang="scss">
.price-trend-tab {
  .control-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    padding: 15px;
    background-color: #f5f7fa;
    border-radius: 4px;

    .left,
    .right {
      display: flex;
      align-items: center;
      gap: 10px;
    }
  }

  .statistics-cards {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 15px;
    margin-bottom: 20px;

    .stat-card {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 20px;
      border-radius: 8px;
      box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);

      .stat-label {
        font-size: 14px;
        opacity: 0.9;
        margin-bottom: 8px;
      }

      .stat-value {
        font-size: 28px;
        font-weight: bold;
      }

      &.positive {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
      }
    }
  }

  .data-tabs {
    :deep(.el-tabs__content) {
      padding: 0;
    }
  }

  .chart-box {
    background-color: white;
    border-radius: 4px;
    padding: 20px;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
    min-height: 400px;
  }
}
</style>
