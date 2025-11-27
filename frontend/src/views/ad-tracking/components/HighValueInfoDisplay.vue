<template>
  <div class="high-value-info-display">
    <el-card shadow="never">
      <!-- 卡片头部 -->
      <template #header>
        <div class="card-header">
          <span class="title">
            <el-icon><DataAnalysis /></el-icon>
            高价值信息展示
          </span>
          <el-button link type="primary" text>
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </template>

      <!-- 空状态 -->
      <el-empty v-if="!hasData" description="暂无高价值信息" />

      <!-- 表格展示 -->
      <el-table
        v-else
        :data="displayData"
        stripe
        :style="{ width: '100%' }"
        :max-height="600"
        v-loading="props.loading"
        element-loading-text="加载中..."
      >
        <!-- 聊天记录内容 -->
        <el-table-column prop="content" label="聊天记录内容" min-width="160">
          <template #default="{ row }">
            <div class="content-cell">
              <span class="text">{{ row.content }}</span>
            </div>
          </template>
        </el-table-column>

        <!-- 聊天图片 -->
        <el-table-column label="图片" width="80" align="center">
          <template #default="{ row }">
            <div v-if="hasImages(row)" class="image-preview">
              <el-image
                :src="getFirstImage(row)"
                fit="cover"
                style="width: 60px; height: 60px; cursor: pointer"
                @click="openImageInNewWindow(getFirstImage(row))"
              />
            </div>
            <span v-else class="text-muted">--</span>
          </template>
        </el-table-column>

        <!-- 大模型判断 -->
        <el-table-column prop="ai_judgment" label="AI判断" min-width="140">
          <template #default="{ row }">
            <el-tag v-if="row.ai_judgment" type="success" size="small" class="ai-judgment-tag">
              {{ row.ai_judgment }}
            </el-tag>
            <span v-else class="text-muted">--</span>
          </template>
        </el-table-column>

        <!-- 重要程度 -->
        <el-table-column label="重要程度" width="100" align="center" sortable>
          <template #default="{ row }">
            <div class="importance-cell">
              <el-progress
                :percentage="row.importance_score || 0"
                :color="getImportanceColor(row.importance_score)"
                :show-text="false"
                style="margin-bottom: 4px"
              />
              <span class="score">{{ row.importance_score?.toFixed(1) || '-' }}/100</span>
            </div>
          </template>
        </el-table-column>

        <!-- 优先级 -->
        <el-table-column label="优先级" width="90" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.is_high_priority" type="danger" size="small">
              🔴 高
            </el-tag>
            <el-tag v-else type="warning" size="small">
              🟡 中/低
            </el-tag>
          </template>
        </el-table-column>

        <!-- 用户名 -->
        <el-table-column prop="username" label="用户名" width="100" show-overflow-tooltip>
          <template #default="{ row }">
            <span>{{ row.username || '--' }}</span>
          </template>
        </el-table-column>

        <!-- 所属群组 -->
        <el-table-column prop="group_name" label="群组名" min-width="100" show-overflow-tooltip>
          <template #default="{ row }">
            <span>{{ row.group_name || '--' }}</span>
          </template>
        </el-table-column>

        <!-- 发布时间 -->
        <el-table-column prop="publish_time" label="发布时间" width="160" align="center" sortable>
          <template #default="{ row }">
            <span>{{ formatTime(row.publish_time) }}</span>
          </template>
        </el-table-column>

        <!-- 操作 -->
        <el-table-column label="操作" width="120" align="center" fixed="right">
          <template #default="{ row }">
            <el-space wrap>
              <el-button
                type="primary"
                link
                size="small"
                @click="handleViewDetail(row)"
              >
                详情
              </el-button>
              <el-popconfirm
                title="确定删除？"
                confirm-button-text="确定"
                cancel-button-text="取消"
                @confirm="handleDelete(row)"
              >
                <template #reference>
                  <el-button
                    type="danger"
                    link
                    size="small"
                  >
                    删除
                  </el-button>
                </template>
              </el-popconfirm>
            </el-space>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div v-if="hasData" class="pagination-wrapper">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[5, 10, 20]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @current-page-change="handlePageChange"
          @page-size-change="handlePageSizeChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { DataAnalysis, Refresh } from '@element-plus/icons-vue'
import type { AdTracking } from '@/types/adTracking'

interface HighValueInfo extends AdTracking {
  ai_judgment?: string
  username?: string
  group_name?: string
  publish_time?: string
  images?: string[]
}

/**
 * 示例数据格式（供测试使用）
 * {
 *   id: 1,
 *   content: "示例内容文本",
 *   content_type: "url",
 *   normalized_content: "normalized",
 *   source_type: "chat",
 *   source_id: "123",
 *   user_id: "456",
 *   chat_id: "789",
 *   first_seen: "2024-01-01T00:00:00",
 *   last_seen: "2024-01-02T00:00:00",
 *   occurrence_count: 5,
 *   ai_judgment: "风险内容",
 *   username: "testuser",
 *   group_name: "Test Group",
 *   publish_time: "2024-01-01T12:00:00",
 *   images: ["https://example.com/image1.jpg"]
 * }
 */

interface Props {
  data?: HighValueInfo[]
  loading?: boolean
  total?: number
}

const props = withDefaults(defineProps<Props>(), {
  data: () => [],
  loading: false,
  total: 0
})

const emit = defineEmits<{
  (e: 'view-detail', row: HighValueInfo): void
  (e: 'delete', row: HighValueInfo): void
  (e: 'page-change', page: number): void
  (e: 'page-size-change', size: number): void
  (e: 'refresh'): void
}>()

// ==================== 本地状态 ====================

const currentPage = ref(1)
const pageSize = ref(10)

// ==================== Computed ====================

const hasData = computed(() => props.data && props.data.length > 0)

const displayData = computed(() => {
  return props.data || []
})

// ==================== Methods ====================


/**
 * 检查是否有图片
 */
function hasImages(row: HighValueInfo): boolean {
  return !!(row.images && row.images.length > 0)
}

/**
 * 构建完整的图片 URL
 */
function buildImageUrl(imagePath: string): string {
  if (!imagePath) return ''
  // 如果已经是完整 URL，直接返回
  if (imagePath.startsWith('http://') || imagePath.startsWith('https://')) {
    return imagePath
  }
  // 否则，拼接为静态资源路径
  return `/static/${imagePath}`
}

/**
 * 获取第一张图片
 */
function getFirstImage(row: HighValueInfo): string {
  const imagePath = row.images?.[0]
  return imagePath ? buildImageUrl(imagePath) : ''
}


/**
 * 格式化时间
 */
function formatTime(time?: string): string {
  if (!time) return '--'
  return new Date(time).toLocaleString('zh-CN')
}

/**
 * 查看详情
 */
function handleViewDetail(row: HighValueInfo) {
  emit('view-detail', row)
}

/**
 * 删除
 */
function handleDelete(row: HighValueInfo) {
  emit('delete', row)
}

/**
 * 分页变化
 */
function handlePageChange(page: number) {
  currentPage.value = page
  emit('page-change', page)
}

/**
 * 页面大小变化
 */
function handlePageSizeChange(size: number) {
  pageSize.value = size
  currentPage.value = 1
  emit('page-size-change', size)
}

/**
 * 获取重要程度的颜色
 */
function getImportanceColor(score?: number): string {
  if (!score) return '#909399'
  if (score >= 81) return '#F56C6C'      // 红色 - 极高风险
  if (score >= 61) return '#E6A23C'      // 橙色 - 高风险
  if (score >= 41) return '#409EFF'      // 蓝色 - 中等风险
  if (score >= 21) return '#67C23A'      // 绿色 - 低风险
  return '#909399'                       // 灰色 - 无风险
}

/**
 * 在新窗口打开图片
 */
function openImageInNewWindow(imageUrl: string) {
  if (imageUrl) {
    window.open(imageUrl, '_blank')
  }
}
</script>

<style scoped lang="scss">
.high-value-info-display {
  margin-bottom: 20px;

  :deep(.el-card__header) {
    padding: 16px 20px;
    border-bottom: 1px solid #ebeef5;
  }

  :deep(.el-card__body) {
    padding: 20px;
  }

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;

    .title {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 14px;
      font-weight: 600;
      color: #303133;

      :deep(.el-icon) {
        font-size: 18px;
        color: #409eff;
      }
    }
  }

  .content-cell {
    .text {
      color: #606266;
      font-size: 13px;
      word-break: break-word;
      white-space: pre-wrap;
      word-wrap: break-word;
      display: inline-block;
      max-width: 100%;
    }
  }

  .image-preview {
    display: flex;
    justify-content: center;
    align-items: center;
  }

  .user-info {
    display: flex;
    align-items: center;
    gap: 8px;

    span {
      color: #606266;
      font-size: 13px;
    }
  }

  .text-muted {
    color: #909399;
    font-size: 13px;
  }

  .pagination-wrapper {
    display: flex;
    justify-content: center;
    margin-top: 20px;
    padding-top: 16px;
    border-top: 1px solid #ebeef5;
  }

  :deep(.el-table) {
    --el-table-border-color: #ebeef5;
    --el-table-header-bg-color: #f5f7fa;
    --el-table-header-text-color: #303133;

    .el-table__header {
      th {
        padding: 12px 0;
        font-weight: 600;
        font-size: 13px;
        background-color: #f5f7fa;
      }
    }

    .el-table__body {
      td {
        padding: 12px 8px;
        font-size: 13px;
        color: #606266;
      }
    }

    .el-table__row {
      height: auto;
    }
  }

  :deep(.el-empty) {
    padding: 40px 20px;
  }

  :deep(.el-tag) {
    font-size: 12px;

    &.ai-judgment-tag {
      white-space: pre-wrap;
      word-break: break-word;
      max-width: 100%;
      height: auto;
      line-height: 1.5;
    }
  }

  .importance-cell {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;

    :deep(.el-progress) {
      flex: 1;
      width: 80px;
    }

    .score {
      font-size: 12px;
      font-weight: 600;
      color: #303133;
    }
  }
}

@media (max-width: 768px) {
  .high-value-info-display {
    :deep(.el-card__header) {
      padding: 12px 15px;
    }

    :deep(.el-card__body) {
      padding: 15px;
    }

    .card-header {
      flex-direction: column;
      gap: 10px;
      align-items: flex-start;
    }

    :deep(.el-table) {
      font-size: 12px;

      .el-table__header th {
        padding: 8px 0;
        font-size: 12px;
      }

      .el-table__body td {
        padding: 8px 0;
        font-size: 12px;
      }
    }
  }
}
</style>
