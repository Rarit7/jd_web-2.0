<template>
  <div class="transaction-methods-tab">
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

    <!-- 图表 -->
    <div class="charts-container" v-loading="loading">
      <div class="chart-box">
        <h3>交易方式分布</h3>
        <TransactionMethodBarChart
          :data="barChartData"
          :loading="loading"
        />
      </div>

      <div class="chart-box">
        <h3>交易方式趋势</h3>
        <div class="legend-controls">
          <el-checkbox-group v-model="visibleMethods" @change="handleMethodsChange">
            <el-checkbox
              v-for="method in barChartData"
              :key="method.id"
              :label="method.name"
            />
          </el-checkbox-group>
        </div>
        <TransactionMethodLineChart
          :data="trendData"
          :visible-methods="visibleMethods"
          :loading="loading"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import {
  useTransactionMethodsStore,
  useAdAnalysisStore
} from '@/store/modules/adAnalysis'
import {
  apiGetTransactionMethods,
  apiGetTransactionMethodsTrend
} from '@/api/adAnalysis'
import TransactionMethodBarChart from './TransactionMethodBarChart.vue'
import TransactionMethodLineChart from './TransactionMethodLineChart.vue'
import type {
  TransactionMethodData,
  TransactionMethodTrendData
} from '@/types/adAnalysis'

// Stores
const transactionMethodsStore = useTransactionMethodsStore()
const analysisStore = useAdAnalysisStore()

// State
const loading = ref(false)
const barChartData = ref<TransactionMethodData[]>([])
const trendData = ref<TransactionMethodTrendData | null>(null)
const visibleMethods = ref<string[]>([])
const selectedDays = ref(365)

// Methods
async function loadMethods() {
  try {
    await transactionMethodsStore.fetchMethods()
  } catch (error) {
    ElMessage.error('加载交易方式失败')
  }
}

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
    const [barResponse, trendResponse] = await Promise.all([
      apiGetTransactionMethods(params),
      apiGetTransactionMethodsTrend(params)
    ])

    // 后端返回的是 {bar: [...]} 而不是 {data: [...]}
    barChartData.value = barResponse.payload.bar || []
    // 后端返回的是 {line: {months, data}} 而不是直接返回 {months, data}
    trendData.value = trendResponse.payload.line || null

    // 初始化显示所有方法
    visibleMethods.value = barChartData.value.map(m => m.name)

    transactionMethodsStore.setBarChartData(barChartData.value)
    transactionMethodsStore.setTrendData(trendData.value)
    transactionMethodsStore.setVisibleMethods(visibleMethods.value)
  } catch (error) {
    console.error('加载数据失败:', error)
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  loadData()
}

function handleReset() {
  selectedDays.value = 365
  transactionMethodsStore.reset()
  loadData()
}

function handleMethodsChange() {
  transactionMethodsStore.setVisibleMethods(visibleMethods.value)
}

// Lifecycle
onMounted(async () => {
  await loadMethods()
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
.transaction-methods-tab {
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

  .charts-container {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
    padding: 20px;

    @media (max-width: 1200px) {
      grid-template-columns: 1fr;
    }

    .chart-box {
      background-color: white;
      border-radius: 4px;
      padding: 20px;
      box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);

      h3 {
        margin: 0 0 15px 0;
        font-size: 16px;
        font-weight: 600;
        color: #303133;
      }

      .legend-controls {
        margin-bottom: 15px;
        padding: 10px;
        background-color: #f5f7fa;
        border-radius: 4px;

        :deep(.el-checkbox__label) {
          margin-right: 15px;
        }
      }

      > div:last-child {
        min-height: 400px;
      }
    }
  }
}
</style>
