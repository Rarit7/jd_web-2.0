<template>
  <el-dialog
    v-model="dialogVisible"
    title="批次详情"
    width="900px"
    :before-close="handleClose"
    destroy-on-close
  >
    <div v-loading="loading" class="batch-detail-container">
      <!-- 基本信息 -->
      <el-descriptions title="批次信息" :column="3" border>
        <el-descriptions-item label="批次ID">
          {{ batch?.id }}
        </el-descriptions-item>
        <el-descriptions-item label="频道ID">
          {{ batch?.channel_id }}
        </el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusType(batch?.status)" size="large">
            {{ getStatusText(batch?.status) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="选中的标签" :span="2">
          <el-tag
            v-for="tagId in batch?.selected_tag_ids"
            :key="tagId"
            size="small"
            type="danger"
            effect="light"
            style="margin-right: 4px; margin-bottom: 4px"
          >
            {{ getTagName(tagId) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="任务ID" :span="1">
          {{ batch?.task_id || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">
          {{ formatDateTime(batch?.created_at) }}
        </el-descriptions-item>
        <el-descriptions-item label="更新时间">
          {{ formatDateTime(batch?.updated_at) }}
        </el-descriptions-item>
      </el-descriptions>

      <!-- 处理进度 -->
      <div class="progress-section">
        <h4>处理进度</h4>
        <div class="progress-container">
          <el-progress
            type="dashboard"
            :percentage="batch?.progress || 0"
            :status="getProgressStatus(batch)"
            :width="200"
            :stroke-width="12"
          >
            <template #default="{ percentage }">
              <div class="progress-content">
                <span class="percentage-text">{{ percentage }}%</span>
                <div class="progress-stats">
                  <div class="stat-item">
                    <span class="stat-label">已处理:</span>
                    <span class="stat-value">{{ batch?.processed_messages || 0 }}</span>
                  </div>
                  <div class="stat-item">
                    <span class="stat-label">总数:</span>
                    <span class="stat-value">{{ batch?.total_messages || 0 }}</span>
                  </div>
                  <div class="stat-item">
                    <span class="stat-label">已创建:</span>
                    <span class="stat-value text-success">{{ batch?.created_messages || 0 }}</span>
                  </div>
                </div>
              </div>
            </template>
          </el-progress>
        </div>
      </div>

      <!-- 任务信息 -->
      <div v-if="batch?.task_info" class="task-section">
        <h4>Celery 任务信息</h4>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="任务ID">
            {{ batch.task_info.task_id }}
          </el-descriptions-item>
          <el-descriptions-item label="任务状态">
            {{ batch.task_info.state }}
          </el-descriptions-item>
          <el-descriptions-item label="当前进度" :span="2">
            {{ batch.task_info.info?.current || 0 }} / {{ batch.task_info.info?.total || 0 }}
          </el-descriptions-item>
        </el-descriptions>
      </div>

      <!-- 错误信息 -->
      <div v-if="batch?.error_message" class="error-section">
        <h4>错误信息</h4>
        <el-alert
          :title="batch.error_message"
          type="error"
          :closable="false"
          show-icon
        />
      </div>

      <!-- 操作记录 -->
      <div class="timeline-section">
        <h4>操作记录</h4>
        <el-timeline>
          <el-timeline-item
            v-for="(event, index) in timelineEvents"
            :key="index"
            :timestamp="formatDateTime(event.timestamp)"
            :type="event.type"
          >
            <el-card>
              <h5>{{ event.title }}</h5>
              <p class="event-description">{{ event.description }}</p>
            </el-card>
          </el-timeline-item>
        </el-timeline>
      </div>
    </div>

    <!-- 底部操作 -->
    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">关闭</el-button>
        <template v-if="canRetry(batch)">
          <el-button type="warning" @click="handleRetry">
            <el-icon><RefreshRight /></el-icon>
            重试
          </el-button>
        </template>
        <template v-if="canCancel(batch)">
          <el-button type="danger" @click="handleCancel">
            <el-icon><Close /></el-icon>
            取消
          </el-button>
        </template>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { RefreshRight, Close } from '@element-plus/icons-vue'
import adTrackingApi from '@/api/adTracking'
import type { AdTrackingBatch, AdTrackingTag } from '@/types/adTracking'

const props = defineProps<{
  modelValue: boolean
  batch: AdTrackingBatch | null
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  retried: []
  cancelled: []
}>()

const loading = ref(false)
const tags = ref<AdTrackingTag[]>([])

// 计算属性
const dialogVisible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

// 计算时间线事件
const timelineEvents = computed(() => {
  if (!props.batch) return []

  const events = []

  // 创建事件
  if (props.batch.created_at) {
    events.unshift({
      timestamp: props.batch.created_at,
      type: 'primary',
      title: '批次创建',
      description: '创建了一个新的广告处理批次'
    })
  }

  // 开始事件
  if (props.batch.started_at) {
    events.unshift({
      timestamp: props.batch.started_at,
      type: 'success',
      title: '处理开始',
      description: '开始处理频道的聊天记录'
    })
  }

  // 完成事件
  if (props.batch.completed_at) {
    events.unshift({
      timestamp: props.batch.completed_at,
      type: props.batch.status === 'completed' ? 'success' : 'danger',
      title: props.batch.status === 'completed' ? '处理完成' : '处理失败',
      description: props.batch.status === 'completed'
        ? `成功处理了 ${props.batch.total_messages || 0} 条消息，创建了 ${props.batch.created_messages || 0} 条广告记录`
        : '处理过程中发生错误，请查看错误信息'
    })
  }

  return events
})

// 加载标签数据
const loadTags = async () => {
  if (tags.value.length > 0) return

  try {
    const response = await adTrackingApi.getTags()
    tags.value = response.data || []
  } catch (error) {
    console.error('加载标签失败:', error)
  }
}

// 获取标签名称
const getTagName = (tagId: number) => {
  const tag = tags.value.find(t => t.id === tagId)
  return tag?.tag_name || tag?.keyword || `标签${tagId}`
}

// 获取状态类型
const getStatusType = (status?: string) => {
  const statusMap: Record<string, string> = {
    'pending': 'info',
    'processing': 'warning',
    'completed': 'success',
    'failed': 'danger',
    'cancelled': 'info'
  }
  return statusMap[status || ''] || 'info'
}

// 获取状态文本
const getStatusText = (status?: string) => {
  const statusMap: Record<string, string> = {
    'pending': '等待中',
    'processing': '处理中',
    'completed': '已完成',
    'failed': '失败',
    'cancelled': '已取消'
  }
  return statusMap[status || ''] || '未知'
}

// 获取进度状态
const getProgressStatus = (batch?: AdTrackingBatch) => {
  if (!batch) return 'normal'
  if (batch.status === 'failed') return 'exception'
  if (batch.status === 'completed') return 'success'
  return 'normal'
}

// 判断是否可以重试
const canRetry = (batch?: AdTrackingBatch) => {
  return batch && (batch.status === 'failed' || batch.status === 'cancelled')
}

// 判断是否可以取消
const canCancel = (batch?: AdTrackingBatch) => {
  return batch && ['pending', 'processing'].includes(batch.status || '')
}

// 格式化日期时间
const formatDateTime = (dateString: string | null) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleString('zh-CN')
}

// 关闭对话框
const handleClose = () => {
  dialogVisible.value = false
}

// 重试批次
const handleRetry = async () => {
  if (!props.batch) return

  try {
    await ElMessageBox.confirm(
      `确定要重试批次 ${props.batch.id} 吗？`,
      '确认重试',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    loading.value = true
    await adTrackingApi.retryBatch(props.batch.id)
    loading.value = false

    ElMessage.success('批次已重新开始')
    emit('retried')
    handleClose()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('重试失败:', error)
      ElMessage.error('重试失败')
    }
    loading.value = false
  }
}

// 取消批次
const handleCancel = async () => {
  if (!props.batch) return

  try {
    await ElMessageBox.confirm(
      `确定要取消批次 ${props.batch.id} 吗？此操作不可恢复。`,
      '确认取消',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'error'
      }
    )

    loading.value = true
    await adTrackingApi.cancelBatch(props.batch.id)
    loading.value = false

    ElMessage.success('批次已取消')
    emit('cancelled')
    handleClose()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('取消失败:', error)
      ElMessage.error('取消失败')
    }
    loading.value = false
  }
}

// 监听批次变化
watch(() => props.batch, (batch) => {
  if (batch && dialogVisible.value) {
    loadTags()
  }
}, { immediate: true })
</script>

<style scoped lang="scss">
.batch-detail-container {
  .progress-section {
    margin: 24px 0;

    h4 {
      margin: 0 0 16px 0;
      font-size: 16px;
      font-weight: 600;
      color: #303133;
    }

    .progress-container {
      display: flex;
      justify-content: center;
      align-items: center;
      padding: 20px;

      .progress-content {
        text-align: center;

        .percentage-text {
          font-size: 32px;
          font-weight: bold;
          color: #303133;
          display: block;
          margin-bottom: 12px;
        }

        .progress-stats {
          display: flex;
          justify-content: center;
          gap: 24px;

          .stat-item {
            display: flex;
            align-items: center;
            gap: 4px;

            .stat-label {
              font-size: 12px;
              color: #909399;
            }

            .stat-value {
              font-weight: 600;
              color: #303133;

              &.text-success {
                color: #67C23A;
              }
            }
          }
        }
      }
    }
  }

  .task-section,
  .error-section,
  .timeline-section {
    margin-top: 24px;

    h4 {
      margin: 0 0 16px 0;
      font-size: 16px;
      font-weight: 600;
      color: #303133;
    }
  }

  .event-description {
    margin: 8px 0 0 0;
    color: #606266;
    font-size: 14px;
  }
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>