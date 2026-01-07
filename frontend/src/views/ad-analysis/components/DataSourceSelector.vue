<template>
  <div class="data-source-selector">
    <!-- 顶部说明信息 -->
    <div class="selector-intro">
      <p class="intro-text">
        选择要分析的频道或群组，支持对聊天记录中的<strong>价格</strong>、<strong>交易方式</strong>、<strong>地理位置</strong>、<strong>黑词</strong>进行提取和分析
      </p>
    </div>

    <!-- 数据源选择卡片 -->
    <el-card shadow="hover" class="selector-card">
      <template #header>
        <div class="card-header">
          <span class="title">
            <el-icon style="margin-right: 8px"><Download /></el-icon>
            选择数据源并开始处理
          </span>
        </div>
      </template>

      <el-form
        ref="selectorFormRef"
        :model="selectorForm"
        :rules="selectorRules"
        label-width="100px"
        class="selector-form"
      >
        <!-- 频道/群组选择 -->
        <el-form-item label="选择源" prop="chat_id">
          <el-select
            v-model="selectorForm.chat_id"
            placeholder="请选择要分析的频道或群组"
            filterable
            remote
            remote-show-suffix
            :remote-method="searchChannels"
            :loading="loadingChannels"
            style="width: 100%"
            @change="handleChannelChange"
          >
            <el-option-group
              v-for="group in channelGroups"
              :key="group.label"
              :label="group.label"
            >
              <el-option
                v-for="channel in group.options"
                :key="channel.id"
                :label="`${channel.name} (${channel.title})`"
                :value="channel.chat_id"
              >
                <div class="channel-option">
                  <div class="channel-header">
                    <div class="channel-name-section">
                      <span class="channel-name">{{ channel.name }}</span>
                      <span class="channel-title">{{ channel.title }}</span>
                    </div>
                    <el-tag
                      :type="getChannelTypeTag(channel.group_type)"
                      size="small"
                    >
                      {{ getChannelTypeText(channel.group_type) }}
                    </el-tag>
                  </div>
                  <div class="channel-meta">
                    <span>{{ formatLastActive(channel.last_active) }}</span>
                    <span v-if="channel.status === 1" class="status-active">活跃</span>
                  </div>
                </div>
              </el-option>
            </el-option-group>
          </el-select>
        </el-form-item>

        <!-- 统计周期选择（可选） -->
        <el-form-item label="统计周期" prop="days">
          <el-select
            v-model="selectorForm.days"
            style="width: 100%"
          >
            <el-option label="近30天" :value="30" />
            <el-option label="近90天" :value="90" />
            <el-option label="近180天" :value="180" />
            <el-option label="近365天" :value="365" />
          </el-select>
        </el-form-item>

        <!-- 操作按钮 -->
        <el-form-item>
          <div class="button-group">
            <el-button
              type="primary"
              @click="submitForm"
              :loading="submitting"
              :disabled="!selectorForm.chat_id"
            >
              <el-icon><VideoPlay /></el-icon>
              {{ submitting ? '数据处理中...' : '开始数据处理' }}
            </el-button>
            <el-button
              type="danger"
              @click="handleClearCache"
              :loading="clearingCache"
              plain
            >
              <el-icon><Delete /></el-icon>
              {{ clearingCache ? '清空中...' : '清空缓存' }}
            </el-button>
            <el-button @click="resetForm">
              重置
            </el-button>
          </div>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 选中源的信息提示 -->
    <el-alert
      v-if="selectedChannelInfo"
      title="已选择数据源"
      :description="selectedChannelInfo"
      type="info"
      closable
      style="margin-top: 20px"
    />

    <!-- 处理进度对话框 -->
    <ProcessingDialog
      v-model="showProcessingDialog"
      :batch-id="currentBatchId"
      :task-id="currentTaskId"
      @completed="handleProcessingCompleted"
      @failed="handleProcessingFailed"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Download, VideoPlay, Delete } from '@element-plus/icons-vue'
import adTrackingApi from '@/api/adTracking'
import { apiClearAnalysisCache } from '@/api/adAnalysis'
import { useAdAnalysisStore } from '@/store/modules/adAnalysis'
import ProcessingDialog from './ProcessingDialog.vue'
import type { AdTrackingChannel } from '@/types/adTracking'

// ==================== 响应式状态 ====================
const loadingChannels = ref(false)
const submitting = ref(false)
const clearingCache = ref(false)
const channels = ref<AdTrackingChannel[]>([])
const searchedChannels = ref<AdTrackingChannel[]>([])
const channelSearchKeyword = ref('')

const selectorFormRef = ref()
const selectorForm = ref({
  chat_id: null as string | null,
  days: 365
})

const selectorRules = {
  chat_id: [
    { required: true, message: '请选择要分析的频道或群组', trigger: 'change' }
  ]
}

// 处理进度状态
const showProcessingDialog = ref(false)
const currentBatchId = ref<string | null>(null)
const currentTaskId = ref<string | null>(null)

// 分析 store
const analysisStore = useAdAnalysisStore()

// ==================== 计算属性 ====================

/**
 * 将频道按类型分组
 */
const channelGroups = computed(() => {
  let sourceList = !channelSearchKeyword.value ? channels.value : searchedChannels.value

  const groups = []

  // 频道组（group_type === 2）
  const channelList = sourceList.filter(c => c.group_type === 2)
  if (channelList.length > 0) {
    groups.push({
      label: '📢 频道',
      options: channelList
    })
  }

  // 群组组（group_type === 1）
  const groupList = sourceList.filter(c => c.group_type === 1)
  if (groupList.length > 0) {
    groups.push({
      label: '👥 群组',
      options: groupList
    })
  }

  return groups
})

/**
 * 选中源的信息文本
 */
const selectedChannelInfo = computed(() => {
  if (!selectorForm.value.chat_id) return null

  const allChannels = [...channels.value, ...searchedChannels.value]
  const selected = allChannels.find(c => c.chat_id === selectorForm.value.chat_id)

  if (!selected) return null

  return `已选择 ${getChannelTypeText(selected.group_type)} "${selected.name}"，统计周期：近 ${selectorForm.value.days} 天`
})

// ==================== 方法 ====================

/**
 * 搜索频道和群组
 */
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
    searchedChannels.value = response.data || []
  } catch (error) {
    console.error('搜索频道失败:', error)
    ElMessage.error('搜索失败，请重试')
  } finally {
    loadingChannels.value = false
  }
}

/**
 * 频道变化处理
 */
const handleChannelChange = (chatId: string) => {
  const selected = channels.value.find(c => c.chat_id === chatId)
  if (selected) {
    analysisStore.selectChat(selected.chat_id)
  }
}

/**
 * 提交表单并开始处理
 */
const submitForm = async () => {
  if (!selectorFormRef.value) return

  try {
    await selectorFormRef.value.validate()

    submitting.value = true

    // 调用后端提交处理任务
    const responseData = await adTrackingApi.submitAnalysisBatch({
      chat_id: selectorForm.value.chat_id!,
      include_price: true,
      include_transaction: true,
      include_geo: true,
      include_dark_keyword: true,
      days: selectorForm.value.days
    })

    const response = responseData || {}

    currentBatchId.value = response.batch_id || null
    currentTaskId.value = response.task_id || null

    ElMessage.success('数据处理任务已提交，处理中...')

    // 显示处理进度对话框
    showProcessingDialog.value = true
  } catch (error: any) {
    console.error('提交处理任务失败:', error)
    ElMessage.error(error?.message || '提交任务失败，请重试')
  } finally {
    submitting.value = false
  }
}

/**
 * 重置表单
 */
const resetForm = () => {
  selectorForm.value = {
    chat_id: null,
    days: 365
  }
  selectorFormRef.value?.clearValidate()
}

/**
 * 手动清空Redis缓存
 */
const handleClearCache = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要清空Redis缓存吗？清空后系统将重新计算统计数据，首次加载可能会稍慢。',
      '清空缓存确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    clearingCache.value = true
    const response = await apiClearAnalysisCache(selectorForm.value.chat_id || undefined)
    const clearedCount = response.payload?.cleared_count || 0

    ElMessage.success(`缓存已清空，共清除 ${clearedCount} 条缓存记录`)
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('清空缓存失败:', error)
      ElMessage.error(error?.message || '清空缓存失败，请重试')
    }
  } finally {
    clearingCache.value = false
  }
}

/**
 * 处理完成回调
 */
const handleProcessingCompleted = async () => {
  ElMessage.success('数据处理完成！')
  showProcessingDialog.value = false

  // 清除缓存以确保显示最新数据
  try {
    const chatId = selectorForm.value.chat_id
    const response = await apiClearAnalysisCache(chatId || undefined)
    console.log('缓存已清除:', response.payload?.cleared_count, '条')
  } catch (error) {
    console.error('清除缓存失败:', error)
    // 清除缓存失败不影响数据处理成功的提示
  }

  // 重置表单
  resetForm()
}

/**
 * 处理失败回调
 */
const handleProcessingFailed = () => {
  showProcessingDialog.value = false
}

/**
 * 获取频道类型标签样式
 */
const getChannelTypeTag = (groupType: number) => {
  return groupType === 2 ? 'primary' : 'success'
}

/**
 * 获取频道类型文本
 */
const getChannelTypeText = (groupType: number) => {
  return groupType === 2 ? '频道' : '群组'
}

/**
 * 格式化最后活跃时间
 */
const formatLastActive = (dateString: string | null) => {
  if (!dateString) return '未知'
  const date = new Date(dateString)
  const now = new Date()
  const diff = now.getTime() - date.getTime()

  const days = Math.floor(diff / 86400000)
  if (days > 0) return `${days}天前活跃`

  const hours = Math.floor(diff / 3600000)
  if (hours > 0) return `${hours}小时前活跃`

  const minutes = Math.floor(diff / 60000)
  if (minutes > 0) return `${minutes}分钟前活跃`

  return '刚刚活跃'
}

// ==================== 生命周期 ====================

/**
 * 初始化加载频道列表
 */
onMounted(async () => {
  try {
    loadingChannels.value = true
    const response = await adTrackingApi.getChannels({
      include_inactive: true
    })
    channels.value = response.data || []
  } catch (error) {
    console.error('加载频道列表失败:', error)
    ElMessage.error('加载频道列表失败')
  } finally {
    loadingChannels.value = false
  }
})
</script>

<style scoped lang="scss">
.data-source-selector {
  padding: 20px;
  background-color: transparent;

  .selector-intro {
    margin-bottom: 20px;
    padding: 12px 16px;
    background-color: #e6f7ff;
    border-left: 4px solid #1890ff;
    border-radius: 2px;

    .intro-text {
      margin: 0;
      color: #0050b3;
      font-size: 14px;
      line-height: 1.6;

      strong {
        color: #1890ff;
        font-weight: 600;
      }
    }
  }

  .selector-card {
    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;

      .title {
        font-weight: 600;
        color: #303133;
        display: flex;
        align-items: center;
      }
    }

    .selector-form {
      .button-group {
        display: flex;
        gap: 10px;
      }

      .channel-option {
        display: flex;
        flex-direction: column;
        gap: 6px;
        padding: 4px 0;

        .channel-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: 10px;

          .channel-name-section {
            display: flex;
            flex-direction: column;
            gap: 2px;
            flex: 1;

            .channel-name {
              font-weight: 500;
              color: #303133;
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

          .status-active {
            color: #67c23a;
            font-weight: 500;
          }
        }
      }
    }
  }
}
</style>
