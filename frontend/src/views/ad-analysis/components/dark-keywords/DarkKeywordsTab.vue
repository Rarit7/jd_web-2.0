<template>
  <div class="dark-keywords-tab">
    <!-- 顶部控制条 -->
    <div class="control-bar">
      <div class="left">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索关键词..."
          clearable
          @change="handleSearch"
          style="width: 250px"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>

        <el-select
          v-model="selectedCategoryId"
          placeholder="选择分类"
          clearable
          @change="handleCategoryChange"
          style="width: 180px; margin-left: 10px"
        >
          <el-option
            v-for="category in darkKeywordsStore.categories"
            :key="category.id"
            :label="category.name"
            :value="category.id"
          />
        </el-select>

        <el-select
          v-model="selectedDrugId"
          placeholder="选择毒品"
          clearable
          :disabled="!availableDrugs.length"
          @change="handleSearch"
          style="width: 180px; margin-left: 10px"
        >
          <el-option
            v-for="drug in availableDrugs"
            :key="drug.id"
            :label="drug.name"
            :value="drug.id"
          />
        </el-select>
      </div>

      <div class="right">
        <el-button type="primary" @click="handleSearch">
          查询
        </el-button>
        <el-button @click="handleReset">
          重置
        </el-button>
      </div>
    </div>

    <!-- 标签页切换 -->
    <el-tabs v-model="activeTab" class="data-tabs">
      <!-- 数据分析 -->
      <el-tab-pane label="数据分析" name="analysis">
        <div class="charts-container" v-loading="loading">
          <div class="chart-row">
            <div class="chart-box">
              <h3>黑词分布</h3>
              <DarkKeywordsPieChart
                :data="pieChartData"
                :loading="loading"
              />
            </div>
            <div class="chart-box">
              <h3>趋势分析</h3>
              <DarkKeywordsTrendChart
                :data="trendChartData"
                :loading="loading"
              />
            </div>
          </div>
          <div class="chart-row">
            <div class="chart-box full-width">
              <h3>关键词云</h3>
              <DarkKeywordsWordCloud
                :data="wordCloudData"
                :loading="loading"
              />
            </div>
          </div>
        </div>
      </el-tab-pane>

      <!-- 数据表格 -->
      <el-tab-pane label="数据表格" name="table">
        <div v-loading="loading">
          <DarkKeywordsTable
            :data="tableData"
            :loading="loading"
            :total="total"
            :page="currentPage"
            :page-size="pageSize"
            @page-change="handlePageChange"
            @delete="handleDelete"
          />
        </div>
      </el-tab-pane>

      <!-- 黑词管理 -->
      <el-tab-pane label="黑词管理" name="management">
        <DarkKeywordManagement />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, storeToRefs } from 'vue'
import { ElMessage } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import {
  useDarkKeywordsStore,
  useAdAnalysisStore
} from '@/store/modules/adAnalysis'
import {
  apiGetDarkKeywordsAnalysis,
  apiDeleteDarkKeyword
} from '@/api/adAnalysis'
import DarkKeywordsPieChart from './DarkKeywordsPieChart.vue'
import DarkKeywordsTrendChart from './DarkKeywordsTrendChart.vue'
import DarkKeywordsWordCloud from './DarkKeywordsWordCloud.vue'
import DarkKeywordsTable from './DarkKeywordsTable.vue'
import DarkKeywordManagement from './DarkKeywordManagement.vue'
import type {
  DarkKeywordData,
  DarkKeywordsPieData,
  DarkKeywordsTrendData
} from '@/types/adAnalysis'

// Stores
const darkKeywordsStore = useDarkKeywordsStore()
const analysisStore = useAdAnalysisStore()

// State
const loading = ref(false)
const activeTab = ref<'analysis' | 'table' | 'management'>('analysis')
const searchKeyword = ref('')
const selectedCategoryId = ref<number | null>(null)
const selectedDrugId = ref<number | null>(null)

const pieChartData = ref<DarkKeywordsPieData[] | null>(null)
const trendChartData = ref<DarkKeywordsTrendData | null>(null)
const tableData = ref<DarkKeywordData[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)

// 词云数据（从 tableData 聚合关键词词频）
const wordCloudData = computed(() => {
  if (!tableData.value || tableData.value.length === 0) {
    return []
  }
  // 聚合关键词词频：相同关键词的 count 相加
  const keywordMap = new Map<string, number>()
  tableData.value.forEach(record => {
    const keyword = record.keyword || ''
    const count = record.count || 0
    if (keyword) {
      keywordMap.set(keyword, (keywordMap.get(keyword) || 0) + count)
    }
  })
  // 转换为数组并按词频降序排序
  return Array.from(keywordMap.entries())
    .map(([name, value]) => ({ name, value }))
    .sort((a, b) => b.value - a.value)
})

// Computed
const availableDrugs = computed(() => {
  if (!selectedCategoryId.value) return []
  const category = darkKeywordsStore.categories.find(
    c => c.id === selectedCategoryId.value
  )
  return category?.drugs || []
})

// Methods
async function loadCategories() {
  try {
    await darkKeywordsStore.fetchCategories()
  } catch (error) {
    ElMessage.error('加载分类失败')
  }
}

async function loadAnalysisData() {
  loading.value = true
  try {
    const params = {
      chat_id: analysisStore.selectedChatId || undefined,
      tag_ids: analysisStore.selectedTagIds.length > 0 ? analysisStore.selectedTagIds : undefined,
      keyword: searchKeyword.value || undefined,
      category: selectedCategoryId.value || undefined,
      drug: selectedDrugId.value || undefined,
      days: analysisStore.days,
      offset: (currentPage.value - 1) * pageSize.value,
      limit: pageSize.value
    }

    const response = await apiGetDarkKeywordsAnalysis(params)
    const payload = response.payload

    pieChartData.value = payload.pie || []
    trendChartData.value = payload.line || null
    tableData.value = payload.table || []
    total.value = payload.total || 0

    darkKeywordsStore.setPieData(pieChartData.value)
    darkKeywordsStore.setTrendData(trendChartData.value)
    darkKeywordsStore.setTableData(tableData.value, total.value)
  } catch (error) {
    console.error('加载数据失败:', error)
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  currentPage.value = 1
  loadAnalysisData()
}

function handleReset() {
  searchKeyword.value = ''
  selectedCategoryId.value = null
  selectedDrugId.value = null
  currentPage.value = 1
  darkKeywordsStore.reset()
  loadAnalysisData()
}

function handleCategoryChange() {
  selectedDrugId.value = null
  handleSearch()
}

function handlePageChange(page: number) {
  currentPage.value = page
  loadAnalysisData()
}

async function handleDelete(id: number) {
  try {
    await apiDeleteDarkKeyword(id)
    ElMessage.success('删除成功')
    loadAnalysisData()
  } catch (error) {
    console.error('删除失败:', error)
    ElMessage.error('删除失败')
  }
}

// Lifecycle
onMounted(async () => {
  await loadCategories()
  // 加载全局统计数据
  loadAnalysisData()
})

// Watch for store changes
watch(
  () => analysisStore.selectedChatId,
  () => {
    if (analysisStore.selectedChatId) {
      handleReset()
    }
  }
)
</script>

<style scoped lang="scss">
.dark-keywords-tab {
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

  .data-tabs {
    :deep(.el-tabs__content) {
      padding: 0;
    }
  }

  .charts-container {
    padding: 20px;

    .chart-row {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 20px;
      margin-bottom: 20px;

      @media (max-width: 1200px) {
        grid-template-columns: 1fr;
      }

      .chart-box {
        background-color: white;
        border-radius: 4px;
        padding: 20px;
        box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);

        &.full-width {
          grid-column: 1 / -1;
        }

        h3 {
          margin: 0 0 15px 0;
          font-size: 16px;
          font-weight: 600;
          color: #303133;
        }

        > div {
          min-height: 400px;
        }
      }
    }
  }
}
</style>
