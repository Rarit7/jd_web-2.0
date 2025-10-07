<template>
  <div class="ad-tracking-page">
    <!-- 统计仪表板 -->
    <StatisticsPanel :stats="adTrackingStore.stats" :loading="adTrackingStore.loading.stats" />

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
import { onMounted } from 'vue'
import { useAdTrackingStore } from '@/store/modules/adTracking'
import StatisticsPanel from './components/StatisticsPanel.vue'
import FilterPanel from './components/FilterPanel.vue'
import AdList from './components/AdList.vue'
import DetailDrawer from './components/DetailDrawer.vue'
import type { AdTracking } from '@/types/adTracking'

const adTrackingStore = useAdTrackingStore()

// ==================== 方法 ====================

async function loadData() {
  await Promise.all([
    adTrackingStore.fetchTrackingList(),
    adTrackingStore.fetchStats()
  ])
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
