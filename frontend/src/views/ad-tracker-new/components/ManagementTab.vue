<template>
  <div class="management-tab">
    <!-- 开始处理区域 -->
    <el-card shadow="never" class="process-card">
      <template #header>
        <div class="card-header">
          <span>开始处理频道</span>
          <el-tooltip content="选择频道并选择要追踪的关键词标签，开始处理频道中的广告内容" placement="top">
            <el-icon><QuestionFilled /></el-icon>
          </el-tooltip>
        </div>
      </template>

      <el-form
        ref="processFormRef"
        :model="processForm"
        :rules="processRules"
        label-width="120px"
        class="process-form"
      >
        <el-form-item label="选择频道" prop="channel_id">
          <el-select
            v-model="processForm.channel_id"
            placeholder="请选择要处理的频道"
            filterable
            remote
            remote-show-suffix
            :remote-method="searchChannels"
            :loading="loadingChannels"
            style="width: 100%"
            @change="handleChannelChange"
          >
            <el-option
              v-for="channel in filteredChannels"
              :key="channel.id"
              :label="`${channel.name} (${channel.title})`"
              :value="channel.id"
            >
              <div class="channel-option">
                <div class="channel-info">
                  <div class="channel-name-title">
                    <span class="channel-name">{{ channel.name }}</span>
                    <span class="channel-title">{{ channel.title }}</span>
                  </div>
                  <el-tag
                    :type="channel.status === 1 ? 'success' : 'info'"
                    size="small"
                  >
                    {{ channel.status === 1 ? '活跃' : '非活跃' }}
                  </el-tag>
                </div>
                <div class="channel-meta">
                  <span class="last-active">{{ formatLastActive(channel.last_active) }}</span>
                </div>
              </div>
            </el-option>
          </el-select>
        </el-form-item>

        <el-form-item label="选择关键词标签" prop="selected_tag_ids">
          <el-select
            v-model="processForm.selected_tag_ids"
            placeholder="选择要追踪的关键词标签（可选）"
            multiple
            filterable
            clearable
            :collapse-tags="true"
            :collapse-tags-tooltip="true"
            style="width: 100%"
          >
            <el-option
              v-for="tag in tags"
              :key="tag.id"
              :label="`${tag.tag_name} (${tag.keyword_count}个关键词)`"
              :value="tag.id"
              :disabled="!tag.is_active"
            />
          </el-select>
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            @click="startProcessing"
            :loading="processing"
            :disabled="!canStartProcessing"
          >
            <el-icon><VideoPlay /></el-icon>
            {{ processing ? '处理中...' : '开始处理' }}
          </el-button>
          <el-button @click="resetProcessForm">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 批次详情对话框 -->
    <BatchDetailDialog
      v-model="showBatchDialog"
      :batch="selectedBatch"
      @retried="handleBatchRetried"
      @cancelled="handleBatchCancelled"
    />

    <!-- 频道详情对话框 -->
    <el-dialog
      v-model="showChannelDialog"
      title="频道信息"
      width="600px"
    >
      <div v-loading="loadingChannelDetail">
        <el-descriptions v-if="channelDetail" :column="2" border>
          <el-descriptions-item label="频道名称">
            {{ channelDetail.name }}
          </el-descriptions-item>
          <el-descriptions-item label="用户名">
            @{{ channelDetail.username }}
          </el-descriptions-item>
          <el-descriptions-item label="类型">
            {{ channelDetail.type === 'group' ? '群组' : '频道' }}
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="channelDetail.status === 1 ? 'success' : 'info'">
              {{ channelDetail.status === 1 ? '活跃' : '非活跃' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="成员数量">
            {{ channelDetail.member_count || 0 }}
          </el-descriptions-item>
          <el-descriptions-item label="最后活跃">
            {{ formatDateTime(channelDetail.last_active) }}
          </el-descriptions-item>
          <el-descriptions-item label="描述" :span="2">
            {{ channelDetail.description || '无描述' }}
          </el-descriptions-item>
        </el-descriptions>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  QuestionFilled,
  VideoPlay
} from '@element-plus/icons-vue'
import adTrackingApi from '@/api/adTracking'
import BatchDetailDialog from './BatchDetailDialog.vue'
import type {
  AdTrackingChannel,
  AdTrackingTag,
  AdTrackingBatch,
  TagOption
} from '@/types/adTracking'

// 响应式状态
const loadingChannels = ref(false)
const loadingChannelDetail = ref(false)
const processing = ref(false)
const channels = ref<AdTrackingChannel[]>([])
const tags = ref<AdTrackingTag[]>([])
const selectedBatch = ref<AdTrackingBatch | null>(null)
const showBatchDialog = ref(false)
const showChannelDialog = ref(false)
const channelDetail = ref<AdTrackingChannel | null>(null)
const channelSearchKeyword = ref('')
const searchedChannels = ref<AdTrackingChannel[]>([])

// 处理表单
const processFormRef = ref()
const processForm = ref({
  channel_id: null as number | null,
  selected_tag_ids: [] as number[]
})

// 表单验证规则
const processRules = {
  channel_id: [
    { required: true, message: '请选择要处理的频道', trigger: 'change' }
  ]
  // selected_tag_ids 现在是可选的，不需要验证规则
}

// 计算属性：过滤后的频道（只显示频道类型，不显示群组）
const filteredChannels = computed(() => {
  let result = !channelSearchKeyword.value ? channels.value : searchedChannels.value
  // 过滤只保留频道（group_type === 2），排除群组（group_type === 1）
  return result.filter(channel => channel.group_type === 2)
})


// 计算属性：是否可以开始处理
const canStartProcessing = computed(() => {
  return (
    processForm.value.channel_id !== null &&
    !processing.value
  )
})

// 方法：搜索频道
const searchChannels = async (keyword: string) => {
  channelSearchKeyword.value = keyword

  if (!keyword) {
    searchedChannels.value = []
    return
  }

  try {
    loadingChannels.value = true
    const response = await adTrackingApi.getChannels({
      search: keyword,
      include_inactive: true
    })
    // 只保留频道类型（group_type === 2），排除群组（group_type === 1）
    searchedChannels.value = (response.data || []).filter(channel => channel.group_type === 2)
  } catch (error) {
    // 搜索失败，清空结果
  } finally {
    loadingChannels.value = false
  }
}

// 方法：频道变化处理
const handleChannelChange = (channelId: number) => {
  const channel = channels.value.find(c => c.id === channelId)
  if (channel) {
    // 可以在这里加载频道的更多信息
  }
}

// 方法：开始处理
const startProcessing = async () => {
  if (!processFormRef.value) return

  try {
    // 验证表单
    await processFormRef.value.validate()

    processing.value = true

    const response = await adTrackingApi.startProcessing({
      channel_id: processForm.value.channel_id!,
      selected_tag_ids: processForm.value.selected_tag_ids
    })

    ElMessage.success(`已开始处理频道，批次ID: ${response.batch_id}`)

    // 重置表单
    resetProcessForm()
  } catch (error) {
    ElMessage.error('开始处理失败')
  } finally {
    processing.value = false
  }
}

// 方法：重置处理表单
const resetProcessForm = () => {
  processForm.value = {
    channel_id: null,
    selected_tag_ids: []
  }
  processFormRef.value?.clearValidate()
}

// 方法：显示批次详情
const showBatchDetail = (batch: AdTrackingBatch) => {
  selectedBatch.value = batch
  showBatchDialog.value = true
}

// 方法：重试批次
const retryBatch = async (batchId: string) => {
  try {
    await ElMessageBox.confirm(
      `确定要重试批次 ${batchId} 吗？`,
      '确认重试',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await adTrackingApi.retryBatch(batchId)
    ElMessage.success('批次已重新开始')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('重试失败')
    }
  }
}

// 方法：取消批次
const cancelBatch = async (batchId: string) => {
  try {
    await ElMessageBox.confirm(
      `确定要取消批次 ${batchId} 吗？`,
      '确认取消',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await adTrackingApi.cancelBatch(batchId)
    ElMessage.success('批次已取消')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('取消失败')
    }
  }
}

// 方法：批次重试回调
const handleBatchRetried = () => {
  // 重新加载时会自动刷新
}

// 方法：批次取消回调
const handleBatchCancelled = () => {
  // 取消后的处理
}

// 工具方法：获取进度状态
const getProgressStatus = (batch: AdTrackingBatch) => {
  if (batch.status === 'failed') return 'exception'
  if (batch.status === 'completed') return 'success'
  if (batch.status === 'processing') return 'warning'
  return ''
}

// 工具方法：获取状态类型
const getStatusType = (status: string) => {
  const statusMap: Record<string, string> = {
    'pending': 'info',
    'processing': 'warning',
    'completed': 'success',
    'failed': 'danger',
    'cancelled': 'info'
  }
  return statusMap[status] || 'info'
}

// 工具方法：获取状态文本
const getStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    'pending': '等待中',
    'processing': '处理中',
    'completed': '已完成',
    'failed': '失败',
    'cancelled': '已取消'
  }
  return statusMap[status] || '未知'
}

// 工具方法：获取标签名称
const getTagName = (tagId: number) => {
  const tag = tags.value.find(t => t.id === tagId)
  return tag?.keyword || `标签${tagId}`
}

// 工具方法：判断是否可以取消
const canCancel = (batch: AdTrackingBatch) => {
  return ['pending', 'processing'].includes(batch.status)
}

// 工具方法：格式化日期时间
const formatDateTime = (dateString: string | null) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleString('zh-CN')
}

// 工具方法：格式化最后活跃时间
const formatLastActive = (dateString: string | null) => {
  if (!dateString) return '未知'
  const date = new Date(dateString)
  const now = new Date()
  const diff = now.getTime() - date.getTime()

  const days = Math.floor(diff / 86400000)
  if (days > 0) return `${days}天前`

  const hours = Math.floor(diff / 3600000)
  if (hours > 0) return `${hours}小时前`

  const minutes = Math.floor(diff / 60000)
  if (minutes > 0) return `${minutes}分钟前`

  return '刚刚'
}

// 生命周期：加载数据
onMounted(async () => {
  // 并行加载频道和标签
  const [channelsRes, tagsRes] = await Promise.all([
    adTrackingApi.getChannels(),
    adTrackingApi.getTags()
  ])

  channels.value = channelsRes.data || []
  tags.value = tagsRes.data || []
})
</script>

<style scoped lang="scss">
.management-tab {
  .process-card {
    margin-bottom: 20px;

    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;

      .header-actions {
        display: flex;
        gap: 8px;
      }
    }

    .process-form {
      .channel-option {
        display: flex;
        flex-direction: column;
        gap: 4px;

        .channel-info {
          display: flex;
          justify-content: space-between;
          align-items: center;

          .channel-name-title {
            display: flex;
            flex-direction: column;
            gap: 2px;
            flex: 1;

            .channel-name {
              font-weight: 500;
            }

            .channel-title {
              font-size: 12px;
              color: #909399;
            }
          }
        }

        .channel-meta {
          display: flex;
          gap: 16px;
          font-size: 12px;
          color: #909399;

          .member-count,
          .last-active {
            white-space: nowrap;
          }
        }
      }
    }
  }
}
</style>