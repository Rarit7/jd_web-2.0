<template>
  <el-dialog
    :model-value="modelValue"
    title="数据处理进度"
    width="600px"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
    @update:model-value="$emit('update:modelValue', $event)"
  >
    <!-- 加载状态 -->
    <div v-loading="isLoading" class="processing-content">
      <!-- 进度信息 -->
      <div v-if="batchInfo" class="progress-section">
        <div class="progress-header">
          <span class="label">处理进度</span>
          <span class="percentage">{{ progressPercent }}%</span>
        </div>

        <el-progress
          :percentage="progressPercent"
          :status="getProgressStatus(batchInfo.status)"
          :indeterminate="isProcessing"
          :duration="10"
        />

        <!-- 详细统计 -->
        <div class="stats-grid">
          <div class="stat-item">
            <div class="stat-label">总消息数</div>
            <div class="stat-value">{{ batchInfo.total_messages }}</div>
          </div>
          <div class="stat-item">
            <div class="stat-label">已处理</div>
            <div class="stat-value">{{ batchInfo.processed_messages }}</div>
          </div>
          <div class="stat-item">
            <div class="stat-label">成功</div>
            <div class="stat-value success">{{ batchInfo.success_count }}</div>
          </div>
          <div class="stat-item">
            <div class="stat-label">失败</div>
            <div class="stat-value error">{{ batchInfo.fail_count }}</div>
          </div>
        </div>

        <!-- 状态信息 -->
        <el-alert
          :title="getStatusText(batchInfo.status)"
          :type="getStatusAlertType(batchInfo.status)"
          :closable="false"
          style="margin-top: 16px"
        >
          <template v-if="batchInfo.error_message">
            {{ batchInfo.error_message }}
          </template>
          <template v-else>
            {{ getStatusDescription(batchInfo.status) }}
          </template>
        </el-alert>

        <!-- 时间信息 -->
        <div class="time-info">
          <div v-if="batchInfo.created_at" class="time-item">
            <span class="label">创建时间：</span>
            <span>{{ formatDateTime(batchInfo.created_at) }}</span>
          </div>
          <div v-if="batchInfo.started_at" class="time-item">
            <span class="label">开始时间：</span>
            <span>{{ formatDateTime(batchInfo.started_at) }}</span>
          </div>
          <div v-if="batchInfo.completed_at" class="time-item">
            <span class="label">完成时间：</span>
            <span>{{ formatDateTime(batchInfo.completed_at) }}</span>
          </div>
        </div>
      </div>

      <!-- 加载中提示 -->
      <div v-else class="loading-prompt">
        <el-icon class="is-loading">
          <Loading />
        </el-icon>
        <p>正在获取处理状态...</p>
      </div>
    </div>

    <!-- 底部按钮 -->
    <template #footer>
      <div class="dialog-footer">
        <el-button @click="$emit('update:modelValue', false)">
          {{ isCompleted ? '关闭' : '后台处理' }}
        </el-button>
        <el-button
          v-if="isCompleted"
          type="primary"
          @click="handleConfirm"
        >
          确定
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, onUnmounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Loading } from '@element-plus/icons-vue'
import adTrackingApi from '@/api/adTracking'

// ==================== Props & Emits ====================

interface Props {
  modelValue: boolean
  batchId: string | null
  taskId: string | null
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: false,
  batchId: null,
  taskId: null
})

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'completed': []
  'failed': []
}>()

// ==================== 响应式状态 ====================

const isLoading = ref(false)
const batchInfo = ref<any>(null)
const pollingInterval = ref<ReturnType<typeof setInterval> | null>(null)
const pollingCount = ref(0)

// ==================== 计算属性 ====================

/**
 * 处理进度百分比
 */
const progressPercent = computed(() => {
  if (!batchInfo.value) return 0
  return batchInfo.value.progress_percent || 0
})

/**
 * 是否在处理中
 */
const isProcessing = computed(() => {
  if (!batchInfo.value) return false
  return batchInfo.value.status === 'processing'
})

/**
 * 是否已完成
 */
const isCompleted = computed(() => {
  if (!batchInfo.value) return false
  return ['completed', 'failed'].includes(batchInfo.value.status)
})

// ==================== 方法 ====================

/**
 * 获取进度条状态
 */
const getProgressStatus = (status: string) => {
  if (status === 'completed') return 'success'
  if (status === 'failed') return 'exception'
  return ''
}

/**
 * 获取状态文本
 */
const getStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    'pending': '等待处理',
    'processing': '处理中',
    'completed': '处理完成',
    'failed': '处理失败'
  }
  return statusMap[status] || '未知状态'
}

/**
 * 获取状态描述
 */
const getStatusDescription = (status: string) => {
  const descMap: Record<string, string> = {
    'pending': '您的处理任务已提交，等待开始处理...',
    'processing': '正在处理您的数据，请耐心等待...',
    'completed': '数据处理已完成！您现在可以查看分析结果。',
    'failed': '处理过程中出现错误，请查看错误信息并重试。'
  }
  return descMap[status] || '处理状态未知'
}

/**
 * 获取状态提示框类型
 */
const getStatusAlertType = (status: string) => {
  const typeMap: Record<string, any> = {
    'pending': 'info',
    'processing': 'warning',
    'completed': 'success',
    'failed': 'error'
  }
  return typeMap[status] || 'info'
}

/**
 * 加载批次信息
 */
const loadBatchInfo = async () => {
  if (!props.batchId) return

  try {
    isLoading.value = true
    const response = await adTrackingApi.getBatchStatus(props.batchId)
    // 响应格式为 { batch_id, status, total_messages, ... }
    batchInfo.value = response
  } catch (error) {
    console.error('获取批次状态失败:', error)
    // 如果是首次加载，显示错误
    if (pollingCount.value === 0) {
      ElMessage.error('获取处理状态失败')
    }
  } finally {
    isLoading.value = false
  }
}

/**
 * 开始轮询
 */
const startPolling = () => {
  // 首次立即加载
  loadBatchInfo()

  // 然后定期轮询（每2秒）
  pollingInterval.value = setInterval(() => {
    pollingCount.value++
    loadBatchInfo()

    // 如果已完成，停止轮询
    if (batchInfo.value && isCompleted.value) {
      stopPolling()

      // 发出完成或失败事件
      if (batchInfo.value.status === 'completed') {
        emit('completed')
      } else if (batchInfo.value.status === 'failed') {
        emit('failed')
      }
    }
  }, 2000)
}

/**
 * 停止轮询
 */
const stopPolling = () => {
  if (pollingInterval.value) {
    clearInterval(pollingInterval.value)
    pollingInterval.value = null
  }
}

/**
 * 确定按钮处理
 */
const handleConfirm = () => {
  emit('update:modelValue', false)
}

/**
 * 格式化日期时间
 */
const formatDateTime = (dateString: string | null) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleString('zh-CN')
}

// ==================== 生命周期 ====================

/**
 * 监听模态框打开
 */
watch(
  () => props.modelValue,
  (newVal) => {
    if (newVal && props.batchId) {
      // 重置轮询计数
      pollingCount.value = 0
      batchInfo.value = null
      startPolling()
    } else {
      stopPolling()
    }
  }
)

/**
 * 组件卸载时清理
 */
onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped lang="scss">
.processing-content {
  min-height: 300px;

  .progress-section {
    .progress-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;

      .label {
        font-weight: 500;
        color: #303133;
      }

      .percentage {
        font-size: 20px;
        font-weight: 600;
        color: #409eff;
      }
    }

    :deep(.el-progress) {
      margin-bottom: 24px;
    }

    .stats-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 12px;
      margin-bottom: 20px;

      .stat-item {
        background-color: #f5f7fa;
        border-radius: 4px;
        padding: 12px;
        text-align: center;

        .stat-label {
          font-size: 12px;
          color: #909399;
          margin-bottom: 6px;
        }

        .stat-value {
          font-size: 20px;
          font-weight: 600;
          color: #303133;

          &.success {
            color: #67c23a;
          }

          &.error {
            color: #f56c6c;
          }
        }
      }
    }

    .time-info {
      margin-top: 20px;
      padding-top: 16px;
      border-top: 1px solid #ebeef5;

      .time-item {
        display: flex;
        justify-content: space-between;
        font-size: 12px;
        color: #606266;
        margin-bottom: 8px;

        .label {
          color: #909399;
        }
      }
    }
  }

  .loading-prompt {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 16px;

    .el-icon {
      font-size: 48px;
      color: #409eff;

      &.is-loading {
        animation: rotating 2s linear infinite;
      }
    }

    p {
      margin: 0;
      color: #606266;
      font-size: 14px;
    }
  }
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

@keyframes rotating {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>
