<template>
  <div class="display-tab">
    <!-- 筛选栏 -->
    <el-card shadow="never" class="filter-card" v-if="!loading">
      <el-form :inline="true" :model="filters" class="filter-form" label-position="left">
        <el-row :gutter="16" align="middle">
          <el-col :xs="24" :sm="12" :md="6" :lg="6">
            <el-form-item label="频道" class="filter-item">
              <el-select
                v-model="filters.channel_id"
                placeholder="选择频道"
                clearable
                filterable
                @change="handleFilterChange"
                class="filter-select"
              >
                <el-option
                  v-for="channel in filteredChannels"
                  :key="channel.id"
                  :label="channel.name"
                  :value="channel.id"
                />
              </el-select>
            </el-form-item>
          </el-col>

          <el-col :xs="24" :sm="12" :md="6" :lg="6">
            <el-form-item label="标签" class="filter-item">
              <el-select
                v-model="filters.trigger_tag_id"
                placeholder="选择标签"
                clearable
                filterable
                @change="handleFilterChange"
                class="filter-select"
              >
                <el-option
                  v-for="tag in tags"
                  :key="tag.id"
                  :label="`${tag.tag_name} (${tag.keyword_count}个关键词)`"
                  :value="tag.id"
                />
              </el-select>
            </el-form-item>
          </el-col>

          <el-col :xs="24" :sm="12" :md="5" :lg="5">
            <el-form-item label="状态" class="filter-item">
              <el-select
                v-model="filters.is_processed"
                placeholder="选择状态"
                clearable
                @change="handleFilterChange"
                class="filter-select"
              >
                <el-option label="未处理" :value="false" />
                <el-option label="已处理" :value="true" />
              </el-select>
            </el-form-item>
          </el-col>

          <el-col :xs="24" :sm="12" :md="7" :lg="7">
            <el-form-item class="filter-actions">
              <el-button-group>
                <el-button type="primary" @click="handleRefresh" :loading="loading">
                  <el-icon><Refresh /></el-icon>
                  <span>刷新</span>
                </el-button>
                <el-button @click="handleExport" :disabled="records.length === 0">
                  <el-icon><Download /></el-icon>
                  <span>导出</span>
                </el-button>
              </el-button-group>

              <el-tag v-if="hasActiveFilters" type="info" size="small" class="filter-badge">
                {{ filterCount }} 个筛选
              </el-tag>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
    </el-card>

    <!-- 加载状态（改进的骨架屏） -->
    <div v-if="loading && records.length === 0" class="loading-container">
      <el-row :gutter="16">
        <el-col
          v-for="i in 20"
          :key="i"
          :xs="24"
          :sm="12"
          :md="6"
          :lg="4.8"
        >
          <el-skeleton animated class="skeleton-card">
            <template #template>
              <el-skeleton-item variant="image" style="height: 140px" />
              <div style="padding: 14px">
                <el-skeleton-item variant="h3" style="width: 50%" />
                <el-skeleton-item variant="text" style="margin-top: 8px" />
                <el-skeleton-item variant="text" style="margin-top: 4px; width: 60%" />
              </div>
            </template>
          </el-skeleton>
        </el-col>
      </el-row>
    </div>

    <!-- 空状态（改进的） -->
    <div v-else-if="records.length === 0" class="empty-container">
      <el-empty :description="emptyDescription" :image-size="180">
        <template #description>
          <p class="empty-description">
            {{ emptyDescription }}
          </p>
        </template>
        <el-button type="primary" @click="handleRefresh">
          <el-icon><Refresh /></el-icon>
          刷新数据
        </el-button>
        <el-button v-if="hasActiveFilters" @click="handleResetFilters">
          清除筛选
        </el-button>
      </el-empty>
    </div>

    <!-- 广告卡片网格 -->
    <div v-else class="ad-grid">
      <!-- 统计摘要栏 -->
      <div class="stats-bar">
        <el-space :size="16" alignment="center" wrap>
          <el-statistic title="当前页" :value="records.length" suffix="条" />
          <el-divider direction="vertical" />
          <el-statistic title="总记录" :value="total" suffix="条" />
          <el-divider direction="vertical" />
          <el-text type="info" size="small">
            显示 {{ startIndex }} - {{ endIndex }} 条，共 {{ totalPages }} 页
          </el-text>
        </el-space>
      </div>

      <!-- 卡片网格（带过渡动画） -->
      <transition-group name="card-list" tag="div" class="cards-container">
        <el-row :gutter="16" key="cards-row">
          <el-col
            :xs="24"
            :sm="12"
            :md="6"
            :lg="4.8"
            v-for="record in records"
            :key="record.id"
            class="ad-card-col"
          >
            <AdCard
              :record="record"
              @click="handleAdClick(record)"
              @process="handleProcessAd(record)"
              @delete="handleDeleteAd(record)"
            />
          </el-col>
        </el-row>
      </transition-group>

      <!-- 分页器（改进的样式） -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="pageSizes"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          background
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </div>

    <!-- 详情对话框 -->
    <DetailDialog
      v-model="showDetailDialog"
      :record="selectedRecord"
      @processed="handleRecordProcessed"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh, Download } from '@element-plus/icons-vue'

// 组件导入
import AdCard from './AdCard.vue'
import DetailDialog from './DetailDialog.vue'

// 组合式函数导入
import { useAdRecords } from '@/composables/ad-tracking/useAdRecords'
import { useAdFilters } from '@/composables/ad-tracking/useAdFilters'
import { usePagination } from '@/composables/ad-tracking/usePagination'

// 工具函数导入
import { generateExportFilename, downloadBlob } from '@/utils/adTracking'
import type { AdTrackingRecord } from '@/types/adTracking'

// ===== 组合式函数初始化 =====
const {
  loading,
  records,
  channels,
  tags,
  total,
  filteredChannels,
  loadAllData,
  updateRecord,
  deleteRecord,
  exportRecords
} = useAdRecords()

const {
  filters,
  hasActiveFilters,
  filterCount,
  resetFilters,
  toApiParams
} = useAdFilters()

// ===== 本地状态 =====
const showDetailDialog = ref(false)
const selectedRecord = ref<AdTrackingRecord | null>(null)

// ===== 方法定义 =====
/**
 * 加载数据（结合筛选和分页）
 */
const loadData = async () => {
  const params = {
    ...toApiParams(),
    page: currentPage.value,
    page_size: pageSize.value
  }
  await loadAllData(params)
}

const {
  currentPage,
  pageSize,
  pageSizes,
  totalPages,
  startIndex,
  endIndex,
  setPage,
  setPageSize,
  reset: resetPagination
} = usePagination({
  defaultPageSize: 20,
  pageSizes: [20, 40, 60, 100],
  onPageChange: loadData
})

// ===== 计算属性 =====
const emptyDescription = computed(() => {
  return hasActiveFilters.value ? '没有符合筛选条件的记录' : '暂无广告记录'
})

// ===== 其他方法 =====
/**
 * 筛选条件变化处理
 */
const handleFilterChange = () => {
  resetPagination()
  loadData()
}

/**
 * 重置筛选条件
 */
const handleResetFilters = () => {
  resetFilters()
  resetPagination()
  loadData()
}

/**
 * 刷新数据
 */
const handleRefresh = () => {
  loadData()
}

/**
 * 导出数据
 */
const handleExport = async () => {
  try {
    const exportParams = {
      format: 'excel' as const,
      ...toApiParams()
    }

    const blob = await exportRecords(exportParams)
    const filename = generateExportFilename('ad_records', 'xlsx')
    downloadBlob(blob, filename)

    ElMessage.success('导出成功')
  } catch (error) {
    ElMessage.error('导出失败')
  }
}

/**
 * 点击广告卡片
 */
const handleAdClick = (record: AdTrackingRecord) => {
  selectedRecord.value = record
  showDetailDialog.value = true
}

/**
 * 处理广告（标记为已处理）
 */
const handleProcessAd = async (record: AdTrackingRecord) => {
  try {
    await ElMessageBox.confirm(
      `确定要标记广告 ${record.id} 为已处理吗？`,
      '确认操作',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await updateRecord(record.id, { is_processed: true })
    ElMessage.success('操作成功')

    // 更新本地数据
    const index = records.value.findIndex(r => r.id === record.id)
    if (index !== -1) {
      records.value[index].is_processed = true
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('操作失败')
    }
  }
}

/**
 * 删除广告记录
 */
const handleDeleteAd = async (record: AdTrackingRecord) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除广告记录 ${record.id} 吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'error'
      }
    )

    await deleteRecord(record.id)
    ElMessage.success('删除成功')

    // 更新本地数据
    records.value = records.value.filter(r => r.id !== record.id)
    total.value--
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

/**
 * 记录已处理回调（来自详情对话框）
 */
const handleRecordProcessed = (recordId: number) => {
  const index = records.value.findIndex(r => r.id === recordId)
  if (index !== -1) {
    records.value[index].is_processed = true
  }
}

/**
 * 分页大小变化
 */
const handleSizeChange = (size: number) => {
  setPageSize(size)
}

/**
 * 页码变化
 */
const handleCurrentChange = (page: number) => {
  setPage(page)
}

// ===== 生命周期 =====
onMounted(() => {
  loadData()
})
</script>

<style scoped lang="scss">
.display-tab {
  .filter-card {
    margin-bottom: 20px;
    border-radius: 8px;

    .filter-form {
      .filter-item {
        margin-bottom: 0;
        width: 100%;

        :deep(.el-form-item__label) {
          font-weight: 500;
          color: #606266;
        }
      }

      .filter-select {
        width: 100%;
      }

      .filter-actions {
        display: flex;
        align-items: center;
        gap: 12px;

        .filter-badge {
          margin-left: 8px;
        }
      }
    }
  }

  .loading-container {
    .skeleton-card {
      margin-bottom: 16px;
      border-radius: 8px;
      overflow: hidden;
    }
  }

  .empty-container {
    padding: 80px 0;
    text-align: center;
    background: white;
    border-radius: 8px;

    .empty-description {
      margin: 12px 0 24px;
      color: #909399;
      font-size: 14px;
    }
  }

  .ad-grid {
    .stats-bar {
      padding: 16px 20px;
      background: white;
      border-radius: 8px;
      margin-bottom: 20px;
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.04);
    }

    .cards-container {
      min-height: 400px;
    }

    .ad-card-col {
      margin-bottom: 16px;

      // 卡片列表过渡
      &.card-list-enter-active,
      &.card-list-leave-active {
        transition: all 0.3s ease;
      }

      &.card-list-enter-from {
        opacity: 0;
        transform: translateY(10px);
      }

      &.card-list-leave-to {
        opacity: 0;
        transform: translateX(-10px);
      }
    }

    .pagination-container {
      margin-top: 32px;
      padding: 20px;
      display: flex;
      justify-content: center;
      background: white;
      border-radius: 8px;
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.04);
    }
  }
}

// 响应式调整
@media (max-width: 1200px) {
  .display-tab .filter-card .filter-form {
    :deep(.el-col) {
      margin-bottom: 12px;
    }
  }
}

@media (max-width: 768px) {
  .display-tab {
    .filter-card {
      margin-bottom: 16px;
    }

    .ad-grid .stats-bar {
      :deep(.el-space) {
        justify-content: center;
      }
    }
  }
}
</style>
