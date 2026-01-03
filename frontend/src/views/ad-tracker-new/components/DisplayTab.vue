<template>
  <div class="display-tab">
    <!-- 筛选栏 -->
    <el-card shadow="never" class="filter-card" v-if="!loading">
      <el-form :inline="true" :model="filters" class="filter-form">
        <el-form-item label="频道">
          <el-select
            v-model="filters.channel_id"
            placeholder="选择频道"
            clearable
            filterable
            @change="handleFilterChange"
            style="width: 200px"
          >
            <el-option
              v-for="channel in filteredChannels"
              :key="channel.id"
              :label="channel.name"
              :value="channel.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="标签">
          <el-select
            v-model="filters.trigger_tag_id"
            placeholder="选择标签"
            clearable
            filterable
            @change="handleFilterChange"
            style="width: 220px"
          >
            <el-option
              v-for="tag in tags"
              :key="tag.id"
              :label="`${tag.tag_name} (${tag.keyword_count}个关键词)`"
              :value="tag.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="处理状态">
          <el-select
            v-model="filters.is_processed"
            placeholder="选择状态"
            clearable
            @change="handleFilterChange"
            style="width: 150px"
          >
            <el-option label="未处理" :value="false" />
            <el-option label="已处理" :value="true" />
          </el-select>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleRefresh" :loading="loading">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </el-form-item>

        <el-form-item>
          <el-button @click="handleExport">
            <el-icon><Download /></el-icon>
            导出
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-container">
      <el-skeleton :rows="5" animated />
    </div>

    <!-- 空状态 -->
    <div v-else-if="records.length === 0" class="empty-container">
      <el-empty description="暂无广告记录">
        <el-button type="primary" @click="handleRefresh">刷新数据</el-button>
      </el-empty>
    </div>

    <!-- 广告卡片网格 -->
    <div v-else class="ad-grid">
      <el-row :gutter="4">
        <el-col
          :xs="24"
          :sm="12"
          :md="6"
          :lg="4.4"
          :xl="4.4"
          v-for="(record, index) in records"
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

      <!-- 分页器 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[20, 40, 60, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
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
import {
  Refresh,
  Download
} from '@element-plus/icons-vue'
import AdCard from './AdCard.vue'
import DetailDialog from './DetailDialog.vue'
import adTrackingApi from '@/api/adTracking'
import type { AdTrackingRecord, AdTrackingChannel, AdTrackingTag } from '@/types/adTracking'

// 状态定义
const loading = ref(false)
const records = ref<AdTrackingRecord[]>([])
const channels = ref<AdTrackingChannel[]>([])
const tags = ref<AdTrackingTag[]>([])
const showDetailDialog = ref(false)
const selectedRecord = ref<AdTrackingRecord | null>(null)

// 分页状态
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

// 筛选条件
const filters = ref({
  channel_id: null as number | null,
  trigger_tag_id: null as number | null,
  is_processed: null as boolean | null
})

// 计算属性：只显示频道类型的数据（不显示群组）
const filteredChannels = computed(() => {
  return channels.value.filter(channel => channel.group_type === 2)
})

// 方法：加载数据
const loadData = async () => {
  loading.value = true
  try {
    // 并行加载所有数据
    const [recordsRes, channelsRes, tagsRes] = await Promise.all([
      adTrackingApi.getRecords({
        page: currentPage.value,
        page_size: pageSize.value,
        ...filters.value
      }),
      adTrackingApi.getChannels(),
      adTrackingApi.getTags()
    ])

    records.value = recordsRes.data || []
    total.value = recordsRes.total || 0
    channels.value = channelsRes.data || []
    tags.value = tagsRes.data || []
  } catch (error) {
    console.error('加载数据失败:', error)
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
}


// 筛选变化处理
const handleFilterChange = () => {
  currentPage.value = 1
  loadData()
}

// 刷新数据
const handleRefresh = () => {
  loadData()
}

// 导出数据
const handleExport = async () => {
  try {
    const exportParams: any = {
      format: 'excel'
    }
    if (filters.value.channel_id) exportParams.channel_id = filters.value.channel_id
    if (filters.value.trigger_tag_id) exportParams.trigger_tag_id = filters.value.trigger_tag_id
    if (filters.value.is_processed !== null) exportParams.is_processed = filters.value.is_processed

    const response = await adTrackingApi.exportRecords(exportParams)

    // 创建下载链接
    const url = window.URL.createObjectURL(new Blob([response]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `ad_records_${new Date().getTime()}.xlsx`)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)

    ElMessage.success('导出成功')
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('导出失败')
  }
}

// 点击广告卡片
const handleAdClick = (record: AdTrackingRecord) => {
  selectedRecord.value = record
  showDetailDialog.value = true
}

// 处理广告
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

    await adTrackingApi.updateRecord(record.id, { is_processed: true })
    ElMessage.success('操作成功')

    // 更新本地数据
    const index = records.value.findIndex(r => r.id === record.id)
    if (index !== -1) {
      records.value[index].is_processed = true
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('处理失败:', error)
      ElMessage.error('操作失败')
    }
  }
}

// 删除广告
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

    await adTrackingApi.deleteRecord(record.id)
    ElMessage.success('删除成功')

    // 更新本地数据
    records.value = records.value.filter(r => r.id !== record.id)
    total.value--
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

// 记录已处理回调
const handleRecordProcessed = (recordId: number) => {
  const index = records.value.findIndex(r => r.id === recordId)
  if (index !== -1) {
    records.value[index].is_processed = true
  }
}

// 分页变化处理
const handleSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1
  loadData()
}

const handleCurrentChange = (page: number) => {
  currentPage.value = page
  loadData()
}

// 生命周期
onMounted(() => {
  loadData()
})
</script>

<style scoped lang="scss">
.display-tab {
  .filter-card {
    margin-bottom: 20px;

    .filter-form {
      .el-form-item {
        margin-bottom: 0;
      }
    }
  }

  .loading-container {
    padding: 20px;
  }

  .empty-container {
    padding: 60px 0;
    text-align: center;
  }

  .ad-grid {
    .ad-card-col {
      margin-bottom: 8px;
    }

    .pagination-container {
      margin-top: 30px;
      display: flex;
      justify-content: center;
    }
  }
}

@media (max-width: 1200px) {
  .display-tab .ad-grid .el-col {
    span: 6;
  }
}

@media (max-width: 768px) {
  .display-tab .ad-grid .el-col {
    span: 12;
  }
}

@media (max-width: 480px) {
  .display-tab .ad-grid .el-col {
    span: 24;
  }
}
</style>