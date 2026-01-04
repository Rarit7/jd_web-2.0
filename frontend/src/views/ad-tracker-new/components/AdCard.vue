<template>
  <el-card
    shadow="hover"
    class="tracker-item-card"
    :class="{ 'processed': record.is_processed }"
    @click="$emit('click', record)"
  >
    <!-- 卡片内容容器：左图片右文字 -->
    <div class="card-content">
      <!-- 左侧：广告图片（方形） -->
      <div class="tracker-image-container" @click.stop>
        <div class="tracker-item-image">
          <img
            v-if="record.image_url"
            :src="record.image_url"
            :alt="record.channel_name"
            @error="handleImageError"
          />
          <img
            v-else
            src="/default-ad.png"
            :alt="record.channel_name"
            @error="handleDefaultImageError"
            class="default-image"
          />
          <div class="no-image">
            <el-icon><Picture /></el-icon>
            <span>暂无图片</span>
          </div>
        </div>
      </div>

      <!-- 右侧：文字信息 -->
      <div class="text-content">
        <!-- 频道信息 -->
        <div class="channel-info">
          <el-tag size="small" type="info" effect="plain" class="channel-tag">
            {{ record.channel_title || record.channel_name }}
          </el-tag>
        </div>

        <!-- 消息预览 -->
        <div class="message-preview">
          <p class="message-text" :class="{ 'processed': record.is_processed }">
            {{ truncateText(record.message_text, 80) }}
          </p>
        </div>

        <!-- 底部：标签、时间、按钮 -->
        <div class="card-footer">
          <!-- 左：标签和时间 -->
          <div class="left-info">
            <!-- 匹配的标签信息 -->
            <div class="matched-tags" v-if="record.tag_info && record.tag_info.length > 0">
              <el-tooltip
                :content="getTagsTooltip"
                placement="top"
              >
                <div class="tags-display">
                  <el-tag
                    v-for="tag in record.tag_info"
                    :key="tag.tag_id"
                    size="small"
                    effect="light"
                    :style="{ backgroundColor: tag.color + '20', borderColor: tag.color, color: tag.color }"
                    class="tag-with-keywords"
                  >
                    <span class="tag-name">{{ tag.tag_name }}</span>
                  </el-tag>
                </div>
              </el-tooltip>
            </div>

            <!-- 或显示触发关键词（向后兼容） -->
            <div class="keyword-tags" v-else-if="record.trigger_keyword">
              <el-tag
                size="small"
                type="danger"
                effect="light"
              >
                {{ record.trigger_keyword }}
              </el-tag>
            </div>

            <!-- 时间信息 -->
            <span class="time-text">{{ formatDateTime(record.send_time) }}</span>
          </div>

          <!-- 右：操作按钮或状态 -->
          <div class="right-actions">
            <!-- 操作按钮组 -->
            <div class="action-buttons" v-if="!record.is_processed">
              <el-button-group size="small">
                <el-button
                  type="primary"
                  @click.stop="$emit('process', record)"
                  title="标记为已处理"
                >
                  <el-icon><Check /></el-icon>
                </el-button>
                <el-button
                  type="danger"
                  @click.stop="$emit('delete', record)"
                  title="删除"
                >
                  <el-icon><Delete /></el-icon>
                </el-button>
              </el-button-group>
            </div>

            <!-- 处理状态标识 -->
            <div v-else class="processed-badge">
              <el-tag size="small" type="success">
                <el-icon><Check /></el-icon>
                已处理
              </el-tag>
            </div>
          </div>
        </div>
      </div>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Picture, Check, Delete } from '@element-plus/icons-vue'
import type { AdTrackingRecord } from '@/types/adTracking'
import { formatDateTime, truncateText } from '@/utils/adTracking'

const props = defineProps<{
  record: AdTrackingRecord
}>()

defineEmits<{
  click: [record: AdTrackingRecord]
  process: [record: AdTrackingRecord]
  delete: [record: AdTrackingRecord]
}>()

// 处理主图片加载错误
const handleImageError = (event: Event) => {
  const img = event.target as HTMLImageElement
  img.style.display = 'none'

  // 显示错误提示
  const noImageElement = img.parentElement?.querySelector('.no-image') as HTMLElement
  if (noImageElement) {
    noImageElement.style.display = 'flex'
    noImageElement.querySelector('span')!.textContent = '图片加载失败'
  }
}

// 处理默认图片加载错误
const handleDefaultImageError = (event: Event) => {
  const img = event.target as HTMLImageElement
  img.style.display = 'none'

  // 显示暂无图片提示
  const noImageElement = img.parentElement?.querySelector('.no-image') as HTMLElement
  if (noImageElement) {
    noImageElement.style.display = 'flex'
    noImageElement.querySelector('span')!.textContent = '暂无图片'
  }
}


// 计算属性：获取标签的 Tooltip 内容
const getTagsTooltip = computed(() => {
  if (!props.record.tag_info || props.record.tag_info.length === 0) return ''

  return props.record.tag_info
    .map(tag => `${tag.tag_name}: ${tag.keywords?.join(', ') || '无关键词'}`)
    .join('\n')
})
</script>

<style scoped lang="scss">
.tracker-item-card {
  cursor: pointer;
  transition: all 0.3s;
  position: relative;
  overflow: hidden;

  :deep(.el-card__body) {
    padding: 8px;
  }

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(0, 0, 0, 0.12);
  }

  &.processed {
    opacity: 0.8;
    border-color: #67C23A;
  }

  // 卡片主容器：左右布局
  .card-content {
    display: flex;
    gap: 12px;
    align-items: stretch;
  }

  // 左侧：图片容器（方形）
  .tracker-image-container {
    flex-shrink: 0;
    width: 120px;
    height: 120px;
    border-radius: 4px;
    overflow: hidden;
    background-color: #f5f7fa;
  }

  .tracker-item-image {
    width: 100%;
    height: 100%;
    overflow: hidden;
    position: relative;
    background-color: #f5f7fa;
    display: flex;
    align-items: center;
    justify-content: center;

    img {
      width: 100%;
      height: 100%;
      object-fit: cover;
      transition: transform 0.3s;

      &:hover {
        transform: scale(1.05);
      }

      &.default-image {
        opacity: 0.6;
      }
    }

    .no-image {
      position: absolute;
      inset: 0;
      display: none;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 4px;
      color: #909399;
      background-color: #f5f7fa;
      font-size: 12px;

      .el-icon {
        font-size: 24px;
      }
    }
  }

  // 右侧：文字内容
  .text-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    min-width: 0;  // 允许文字溢出被截断
  }

  .channel-info {
    flex-shrink: 0;

    .channel-tag {
      font-weight: 500;
      font-size: 12px;
      padding: 2px 6px;
      line-height: 1.2;
      white-space: nowrap;
    }
  }

  .message-preview {
    flex: 1;
    overflow: hidden;
    margin: 4px 0;
    min-height: 0;

    .message-text {
      margin: 0;
      font-size: 13px;
      color: #606266;
      line-height: 1.5;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
      word-break: break-word;

      &.processed {
        color: #909399;
        text-decoration: line-through;
      }
    }
  }

  // 底部：标签、时间、按钮
  .card-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 8px;
    flex-shrink: 0;
    padding-top: 6px;
    border-top: 1px solid #ebeef5;
  }

  .left-info {
    display: flex;
    align-items: center;
    gap: 8px;
    min-width: 0;
    flex: 1;
  }

  .matched-tags {
    flex-shrink: 0;
    display: flex;
    align-items: center;

    .tags-display {
      display: flex;
      flex-wrap: wrap;
      gap: 4px;
      align-items: center;

      .tag-with-keywords {
        padding: 2px 6px !important;
        font-size: 12px;
        line-height: 1.2;
        white-space: nowrap;
        border: 1px solid;
        border-radius: 3px;
        cursor: help;

        .tag-name {
          font-weight: 500;
        }

        .tag-keywords {
          font-size: 11px;
          opacity: 0.8;
          margin-left: 2px;
        }
      }
    }
  }

  .keyword-tags {
    flex-shrink: 0;

    :deep(.el-tag) {
      padding: 2px 6px;
      font-size: 12px;
      line-height: 1;
      white-space: nowrap;
    }
  }

  .time-text {
    font-size: 11px;
    color: #909399;
    white-space: nowrap;
    flex-shrink: 0;
  }

  .right-actions {
    flex-shrink: 0;
    display: flex;
    justify-content: flex-end;
  }

  .action-buttons {
    display: flex;
    gap: 2px;

    :deep(.el-button) {
      padding: 4px 8px;
      font-size: 12px;
      height: auto;
      line-height: 1;
    }
  }

  .processed-badge {
    display: flex;
    justify-content: center;

    :deep(.el-tag) {
      padding: 2px 6px;
      font-size: 12px;
      line-height: 1;
    }
  }
}

// 响应式设计
@media (max-width: 1200px) {
  .tracker-item-card {
    :deep(.el-card__body) {
      padding: 6px;
    }

    .card-content {
      gap: 8px;
    }

    .tracker-image-container {
      width: 100px;
      height: 100px;
    }

    .left-info {
      flex-direction: column;
      align-items: flex-start;
      gap: 2px;
    }

    .time-text {
      font-size: 10px;
    }
  }
}

@media (max-width: 768px) {
  .tracker-item-card {
    .tracker-image-container {
      width: 80px;
      height: 80px;
    }

    .message-preview .message-text {
      font-size: 12px;
      -webkit-line-clamp: 1;
    }

    .left-info {
      flex-direction: column;
      align-items: flex-start;
    }

    .card-footer {
      flex-wrap: wrap;
    }
  }
}
</style>
