<template>
  <div class="ad-list">
    <el-card shadow="never">
      <el-table
        v-loading="loading"
        :data="trackingList"
        stripe
        highlight-current-row
        @row-click="handleRowClick"
        style="width: 100%"
      >
        <el-table-column prop="content" label="广告内容" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            <div class="content-cell">
              <el-text truncated>{{ row.content }}</el-text>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="merchant_name" label="商家名称" width="150" show-overflow-tooltip>
          <template #default="{ row }">
            <span v-if="row.merchant_name" class="merchant-name">{{ row.merchant_name }}</span>
            <span v-else class="empty-text">-</span>
          </template>
        </el-table-column>

        <el-table-column prop="content_type" label="类型" width="130">
          <template #default="{ row }">
            <el-tag :type="getContentTypeTagType(row.content_type)" size="small">
              {{ getContentTypeLabel(row.content_type) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="source_type" label="来源" width="120">
          <template #default="{ row }">
            <div class="source-cell">
              <el-icon>
                <component :is="getSourceIcon(row.source_type)" />
              </el-icon>
              <span>{{ getSourceTypeLabel(row.source_type) }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="tag_ids" label="标签" width="150">
          <template #default="{ row }">
            <div v-if="row.tag_ids && row.tag_ids.length > 0" class="tags-cell">
              <el-tag v-for="(tagId, index) in row.tag_ids.slice(0, 2)" :key="tagId" size="small" style="margin-right: 4px">
                标签{{ tagId }}
              </el-tag>
              <el-tag v-if="row.tag_ids.length > 2" size="small" type="info">
                +{{ row.tag_ids.length - 2 }}
              </el-tag>
            </div>
            <span v-else class="empty-text">-</span>
          </template>
        </el-table-column>

        <el-table-column prop="occurrence_count" label="出现次数" width="100" sortable>
          <template #default="{ row }">
            <el-badge :value="row.occurrence_count" :max="999" type="primary" />
          </template>
        </el-table-column>

        <el-table-column prop="first_seen" label="首次发现" width="160" sortable>
          <template #default="{ row }">
            {{ formatDateTime(row.first_seen) }}
          </template>
        </el-table-column>

        <el-table-column prop="last_seen" label="最后发现" width="160" sortable>
          <template #default="{ row }">
            {{ formatDateTime(row.last_seen) }}
          </template>
        </el-table-column>

        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click.stop="handleViewDetail(row)">
              查看详情
            </el-button>
            <el-button link type="danger" size="small" @click.stop="handleDelete(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessageBox, ElMessage } from 'element-plus'
import { ChatLineRound, User, ChatDotRound, Document } from '@element-plus/icons-vue'
import type { AdTracking } from '@/types/adTracking'
import dayjs from 'dayjs'

interface Props {
  trackingList: AdTracking[]
  loading?: boolean
  total: number
  page: number
  pageSize: number
}

interface Emits {
  (e: 'view-detail', tracking: AdTracking): void
  (e: 'delete', tracking: AdTracking): void
  (e: 'page-change', page: number): void
  (e: 'size-change', size: number): void
}

const props = withDefaults(defineProps<Props>(), {
  loading: false
})

const emit = defineEmits<Emits>()

const currentPage = computed({
  get: () => props.page,
  set: (val) => emit('page-change', val)
})

const pageSize = computed({
  get: () => props.pageSize,
  set: (val) => emit('size-change', val)
})

// ==================== 标签映射 ====================

const contentTypeLabels: Record<string, string> = {
  url: 'URL',
  telegram_account: '@账户',
  t_me_invite: 't.me邀请',
  t_me_channel_msg: 't.me频道',
  t_me_private_invite: 't.me私聊',
  telegraph: 'Telegraph'
}

const sourceTypeLabels: Record<string, string> = {
  chat: '聊天消息',
  user_desc: '用户简介',
  username: '用户名',
  nickname: '昵称',
  group_intro: '群组简介'
}

// ==================== 方法 ====================

function getContentTypeLabel(type: string): string {
  return contentTypeLabels[type] || type
}

function getContentTypeTagType(type: string): string {
  const typeMap: Record<string, string> = {
    url: '',
    telegram_account: 'success',
    t_me_invite: 'warning',
    t_me_channel_msg: 'info',
    t_me_private_invite: 'danger',
    telegraph: 'primary'
  }
  return typeMap[type] || ''
}

function getSourceTypeLabel(type: string): string {
  return sourceTypeLabels[type] || type
}

function getSourceIcon(type: string): any {
  const iconMap: Record<string, any> = {
    chat: ChatLineRound,
    user_desc: User,
    username: User,
    nickname: User,
    group_intro: ChatDotRound
  }
  return iconMap[type] || Document
}

function formatDateTime(dateStr: string): string {
  if (!dateStr) return '-'
  return dayjs(dateStr).format('YYYY-MM-DD HH:mm')
}

function handleRowClick(row: AdTracking) {
  emit('view-detail', row)
}

function handleViewDetail(row: AdTracking) {
  emit('view-detail', row)
}

async function handleDelete(row: AdTracking) {
  try {
    await ElMessageBox.confirm(
      '确定要删除这条广告追踪记录吗？此操作不可恢复。',
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    emit('delete', row)
  } catch {
    // 用户取消
  }
}

function handlePageChange(page: number) {
  emit('page-change', page)
}

function handleSizeChange(size: number) {
  emit('size-change', size)
}
</script>

<style scoped lang="scss">
.ad-list {
  :deep(.el-card__body) {
    padding: 0;
  }

  .el-table {
    .content-cell {
      .el-text {
        max-width: 100%;
      }
    }

    .source-cell {
      display: flex;
      align-items: center;
      gap: 4px;

      .el-icon {
        font-size: 14px;
      }
    }

    .tags-cell {
      display: flex;
      flex-wrap: wrap;
      gap: 4px;
    }

    .empty-text {
      color: #c0c4cc;
      font-size: 12px;
    }
  }

  .pagination-wrapper {
    padding: 20px;
    display: flex;
    justify-content: flex-end;
    background-color: #fff;
    border-top: 1px solid #ebeef5;
  }
}

// 响应式
@media (max-width: 768px) {
  .ad-list {
    .pagination-wrapper {
      padding: 15px;

      :deep(.el-pagination) {
        justify-content: center;

        .el-pagination__sizes,
        .el-pagination__jump {
          display: none;
        }
      }
    }
  }
}
</style>
