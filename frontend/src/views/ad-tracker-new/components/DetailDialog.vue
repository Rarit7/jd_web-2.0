<template>
  <el-dialog
    v-model="dialogVisible"
    title="广告详情"
    width="800px"
    :before-close="handleClose"
    destroy-on-close
  >
    <div v-loading="loading" class="detail-container">
      <!-- 基本信息区 -->
      <el-descriptions :column="2" border>
        <el-descriptions-item label="处理状态">
          <el-tag :type="record?.is_processed ? 'success' : 'warning'">
            {{ record?.is_processed ? '已处理' : '未处理' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="频道名称">
          {{ record?.channel_title || record?.channel_name }}
        </el-descriptions-item>
        <el-descriptions-item label="发送人">
          {{ record?.sender_nickname || record?.sender_id }}
        </el-descriptions-item>
        <el-descriptions-item label="发送时间">
          {{ formatDateTime(record?.send_time) }}
        </el-descriptions-item>
        <el-descriptions-item v-if="record?.trigger_keyword" label="触发关键词" span="2">
          <el-tag type="danger" effect="light">
            {{ record.trigger_keyword }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item v-if="record?.tag_info && record.tag_info.length > 0" label="标签" span="2">
          <div class="tags-container">
            <el-tag
              v-for="tag in record.tag_info"
              :key="tag.tag_id"
              size="small"
              effect="light"
              :style="{ backgroundColor: tag.color + '20', borderColor: tag.color, color: tag.color }"
            >
              {{ tag.tag_name }}
            </el-tag>
          </div>
        </el-descriptions-item>
      </el-descriptions>

      <!-- 消息内容区 -->
      <div class="message-section">
        <h4>消息内容</h4>
        <div class="message-content">
          <div class="message-text-display" v-html="highlightedMessageText"></div>
        </div>
      </div>

      <!-- 图片预览区 -->
      <div v-if="record?.image_url" class="image-section">
        <h4>广告图片</h4>
        <div class="image-preview">
          <el-image
            :src="record.image_url"
            fit="contain"
            :preview-src-list="[record.image_url]"
            style="width: 100%; height: 300px"
            @error="handleImageError"
          >
            <template #error>
              <div class="image-error">
                <el-icon><Picture /></el-icon>
                <p>图片加载失败</p>
              </div>
            </template>
          </el-image>
          <div class="image-actions">
            <el-button
              type="primary"
              text
              @click="openImageInNewTab"
            >
              <el-icon><View /></el-icon>
              在新窗口查看
            </el-button>
            <el-button
              text
              @click="downloadImage"
            >
              <el-icon><Download /></el-icon>
              下载图片
            </el-button>
          </div>
        </div>
      </div>

    </div>

    <!-- 底部操作区 -->
    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">关闭</el-button>
        <template v-if="!record?.is_processed">
          <el-button type="primary" @click="handleMarkAsProcessed">
            <el-icon><Check /></el-icon>
            标记为已处理
          </el-button>
          <el-button type="success" @click="handleBatchProcess">
            <el-icon><Operation /></el-icon>
            批量处理
          </el-button>
        </template>
        <el-button type="danger" @click="handleDelete">
          <el-icon><Delete /></el-icon>
          删除记录
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Picture,
  View,
  Download,
  Check,
  Delete,
  Operation
} from '@element-plus/icons-vue'
import adTrackingApi from '@/api/adTracking'
import { formatDateTime } from '@/utils/adTracking'
import type { AdTrackingRecord, AdTrackingBatch, RelatedRecord } from '@/types/adTracking'

const props = defineProps<{
  modelValue: boolean
  record: AdTrackingRecord | null
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'processed': [recordId: number]
}>()

// 响应式状态
const loading = ref(false)

// 计算属性
const dialogVisible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

// 计算属性：获取高亮后的消息文本
const highlightedMessageText = computed(() => {
  if (!props.record?.message_text) return ''

  let text = props.record.message_text

  // 如果有 tag_info，高亮所有标签的关键词
  if (props.record.tag_info && props.record.tag_info.length > 0) {
    props.record.tag_info.forEach(tag => {
      if (tag.keywords && tag.keywords.length > 0) {
        tag.keywords.forEach(keyword => {
          // 使用正则表达式进行全局替换，保持大小写敏感
          const regex = new RegExp(`(${escapeRegex(keyword)})`, 'g')
          text = text.replace(regex, `<mark style="background-color: ${tag.color}40; color: ${tag.color}; font-weight: 500; padding: 2px 4px; border-radius: 2px;">$1</mark>`)
        })
      }
    })
  }

  // 对换行符进行处理，保留换行
  text = text.replace(/\n/g, '<br>')

  return text
})

// 辅助函数：转义正则表达式特殊字符
const escapeRegex = (str: string) => {
  return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

// 处理图片加载错误
const handleImageError = () => {
  // 图片加载失败的处理逻辑
}

// 在新窗口打开图片
const openImageInNewTab = () => {
  if (props.record?.image_url) {
    window.open(props.record.image_url, '_blank')
  }
}

// 下载图片
const downloadImage = async () => {
  if (!props.record?.image_url) return

  try {
    const response = await fetch(props.record.image_url)
    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `ad_image_${props.record.id}.jpg`)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)

    ElMessage.success('图片下载成功')
  } catch (error) {
    console.error('下载失败:', error)
    ElMessage.error('图片下载失败')
  }
}

// 关闭对话框
const handleClose = () => {
  dialogVisible.value = false
}

// 标记为已处理
const handleMarkAsProcessed = async () => {
  if (!props.record) return

  try {
    await adTrackingApi.updateRecord(props.record.id, { is_processed: true })
    ElMessage.success('操作成功')
    emit('processed', props.record.id)
    handleClose()
  } catch (error) {
    console.error('操作失败:', error)
    ElMessage.error('操作失败')
  }
}

// 批量处理
const handleBatchProcess = async () => {
  if (!props.record) return

  try {
    await ElMessageBox.confirm(
      `确定要开始批量处理包含关键词 "${props.record.trigger_keyword}" 的相关记录吗？`,
      '确认批量处理',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    // 这里可以调用批量处理的 API
    ElMessage.success('批量处理已开始')
    handleClose()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('批量处理失败:', error)
      ElMessage.error('批量处理失败')
    }
  }
}

// 删除记录
const handleDelete = async () => {
  if (!props.record) return

  try {
    await ElMessageBox.confirm(
      `确定要删除广告记录 ${props.record.id} 吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'error'
      }
    )

    await adTrackingApi.deleteRecord(props.record.id)
    ElMessage.success('删除成功')
    handleClose()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

</script>

<style scoped lang="scss">
.detail-container {
  .el-descriptions {
    margin-bottom: 24px;

    .tags-container {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }
  }

  .message-section,
  .image-section {
    margin-bottom: 24px;

    h4 {
      margin: 0 0 16px 0;
      font-size: 16px;
      font-weight: 600;
      color: #303133;
    }
  }

  .message-content {
    .el-textarea {
      background-color: #f8f9fa;
    }

    .message-text-display {
      background-color: #f8f9fa;
      padding: 12px;
      border: 1px solid #dcdfe6;
      border-radius: 4px;
      font-size: 14px;
      line-height: 1.6;
      color: #606266;
      word-break: break-word;
      white-space: pre-wrap;
      max-height: 300px;
      overflow-y: auto;

      mark {
        background-color: #fff3cd;
        padding: 2px 4px;
        border-radius: 2px;
        font-weight: 500;
      }
    }
  }

  .image-preview {
    position: relative;

    .image-error {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      height: 100%;
      color: #909399;

      .el-icon {
        font-size: 48px;
        margin-bottom: 8px;
      }
    }

    .image-actions {
      margin-top: 12px;
      display: flex;
      justify-content: center;
      gap: 16px;
    }
  }

}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>