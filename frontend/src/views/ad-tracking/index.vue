<template>
  <div class="ad-tracking-page">
    <!-- 统计仪表板 -->
    <StatisticsPanel :stats="adTrackingStore.stats" :loading="adTrackingStore.loading.stats" />

    <!-- 高价值信息展示 -->
    <HighValueInfoDisplay
      :data="highValueData"
      :loading="highValueLoading"
      :total="highValueTotal"
      @view-detail="handleViewHighValueDetail"
      @delete="handleDeleteHighValue"
      @page-change="handleHighValuePageChange"
      @page-size-change="handleHighValuePageSizeChange"
    />

    <!-- 筛选面板 -->
    <FilterPanel
      v-model="adTrackingStore.filters"
      @search="handleSearch"
      @reset="handleReset"
    />

    <!-- 广告列表 -->
    <AdList
      :tracking-list="adTrackingStore.trackingList"
      :loading="adTrackingStore.loading.list"
      :total="adTrackingStore.pagination.total"
      :page="adTrackingStore.pagination.page"
      :page-size="adTrackingStore.pagination.pageSize"
      @view-detail="handleViewDetail"
      @delete="handleDelete"
      @page-change="handlePageChange"
      @size-change="handleSizeChange"
    />

    <!-- 详情侧边栏 -->
    <DetailDrawer />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAdTrackingStore } from '@/store/modules/adTracking'
import StatisticsPanel from './components/StatisticsPanel.vue'
import FilterPanel from './components/FilterPanel.vue'
import AdList from './components/AdList.vue'
import DetailDrawer from './components/DetailDrawer.vue'
import HighValueInfoDisplay from './components/HighValueInfoDisplay.vue'
import { getHighValueMessages, deleteHighValueMessage } from '@/api/adTracking'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { AdTracking } from '@/types/adTracking'

const adTrackingStore = useAdTrackingStore()

// ==================== 本地状态 ====================

// 高价值信息数据
const highValueData = ref<any[]>([])
const highValueTotal = ref(0)
const highValuePage = ref(1)
const highValuePageSize = ref(10)
const highValueLoading = ref(false)

// ==================== 方法 ====================

async function loadData() {
  await Promise.all([
    adTrackingStore.fetchTrackingList(),
    adTrackingStore.fetchStats(),
    loadHighValueData()
  ])
}

/**
 * 加载高价值信息数据
 */
async function loadHighValueData() {
  try {
    highValueLoading.value = true
    const response = await getHighValueMessages({
      page: highValuePage.value,
      page_size: highValuePageSize.value,
      sort_by: 'importance_score',
      sort_order: 'desc'
    })
    if (response.data.err_code === 0) {
      highValueData.value = response.data.payload.data
      highValueTotal.value = response.data.payload.total
    } else {
      ElMessage.error(response.data.err_msg || '加载高价值信息失败')
    }
  } catch (error) {
    console.error('加载高价值信息失败:', error)
    ElMessage.error('加载高价值信息失败')
  } finally {
    highValueLoading.value = false
  }
}

function handleSearch() {
  adTrackingStore.fetchTrackingList(true)
}

function handleReset() {
  adTrackingStore.resetFilters()
  loadData()
}

async function handleViewDetail(tracking: AdTracking) {
  await adTrackingStore.fetchTrackingDetail(tracking.id)
}

async function handleDelete(tracking: AdTracking) {
  await adTrackingStore.deleteTracking(tracking.id)
}

function handlePageChange(page: number) {
  adTrackingStore.setPage(page)
  adTrackingStore.fetchTrackingList()
}

function handleSizeChange(size: number) {
  adTrackingStore.setPageSize(size)
  adTrackingStore.fetchTrackingList()
}

// ==================== 高价值信息处理 ====================

function handleViewHighValueDetail(tracking: any) {
  // 查看详情
  adTrackingStore.setDetailDrawerData({
    id: tracking.id,
    content: tracking.content,
    ai_judgment: tracking.ai_judgment,
    username: tracking.username,
    group_name: tracking.group_name,
    publish_time: tracking.publish_time,
    importance_score: tracking.importance_score,
    is_high_priority: tracking.is_high_priority,
    images: tracking.images
  })
  adTrackingStore.openDetailDrawer()
}

async function handleDeleteHighValue(tracking: any) {
  try {
    await ElMessageBox.confirm(
      '确定要删除这条高价值信息吗？',
      '警告',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    const response = await deleteHighValueMessage(tracking.id)
    if (response.data.err_code === 0) {
      ElMessage.success('删除成功')
      await loadHighValueData()
    } else {
      ElMessage.error(response.data.err_msg || '删除失败')
    }
  } catch (error) {
    if (error === 'cancel') {
      return
    }
    console.error('删除失败:', error)
    ElMessage.error('删除失败')
  }
}

async function handleHighValuePageChange(page: number) {
  highValuePage.value = page
  await loadHighValueData()
}

async function handleHighValuePageSizeChange(size: number) {
  highValuePageSize.value = size
  highValuePage.value = 1
  await loadHighValueData()
}

// ==================== 生命周期 ====================

onMounted(() => {
  loadData()
})
</script>

<style scoped lang="scss">
.ad-tracking-page {
  padding: 20px;
  background-color: #f5f7fa;
  min-height: calc(100vh - 60px);
}

@media (max-width: 768px) {
  .ad-tracking-page {
    padding: 10px;
  }
}
</style>
