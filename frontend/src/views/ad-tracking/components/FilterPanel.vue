<template>
  <div class="filter-panel">
    <el-card shadow="never">
      <el-form :model="localFilters" label-width="90px" label-position="left">
        <el-row :gutter="20">
          <!-- 内容类型 -->
          <el-col :xs="24" :sm="12" :md="8" :lg="6">
            <el-form-item label="内容类型">
              <el-select
                v-model="localFilters.contentTypes"
                multiple
                collapse-tags
                collapse-tags-tooltip
                placeholder="请选择"
                clearable
                style="width: 100%"
              >
                <el-option
                  v-for="item in contentTypeOptions"
                  :key="item.value"
                  :label="item.label"
                  :value="item.value"
                />
              </el-select>
            </el-form-item>
          </el-col>

          <!-- 来源类型 -->
          <el-col :xs="24" :sm="12" :md="8" :lg="6">
            <el-form-item label="来源类型">
              <el-select
                v-model="localFilters.sourceTypes"
                multiple
                collapse-tags
                collapse-tags-tooltip
                placeholder="请选择"
                clearable
                style="width: 100%"
              >
                <el-option
                  v-for="item in sourceTypeOptions"
                  :key="item.value"
                  :label="item.label"
                  :value="item.value"
                />
              </el-select>
            </el-form-item>
          </el-col>

          <!-- 标签 -->
          <el-col :xs="24" :sm="12" :md="8" :lg="6">
            <el-form-item label="标签">
              <el-select
                v-model="localFilters.tagIds"
                multiple
                collapse-tags
                collapse-tags-tooltip
                placeholder="请选择标签"
                clearable
                filterable
                style="width: 100%"
                :loading="tagsLoading"
              >
                <el-option
                  v-for="tag in tagsList"
                  :key="tag.id"
                  :label="tag.name"
                  :value="tag.id"
                >
                  <span>
                    <el-tag :color="tag.color" size="small" style="margin-right: 8px">
                      {{ tag.name }}
                    </el-tag>
                  </span>
                </el-option>
              </el-select>
            </el-form-item>
          </el-col>

          <!-- 时间范围 -->
          <el-col :xs="24" :sm="12" :md="8" :lg="6">
            <el-form-item label="时间范围">
              <el-date-picker
                v-model="dateRange"
                type="daterange"
                range-separator="至"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
                :shortcuts="dateShortcuts"
                clearable
                style="width: 100%"
              />
            </el-form-item>
          </el-col>

          <!-- 搜索关键词 -->
          <el-col :xs="24" :sm="12" :md="8" :lg="6">
            <el-form-item label="关键词">
              <el-input
                v-model="localFilters.search"
                placeholder="搜索内容"
                clearable
                @keyup.enter="handleSearch"
              >
                <template #prefix>
                  <el-icon><Search /></el-icon>
                </template>
              </el-input>
            </el-form-item>
          </el-col>

          <!-- 排序 -->
          <el-col :xs="24" :sm="12" :md="8" :lg="6">
            <el-form-item label="排序">
              <el-select v-model="sortField" placeholder="选择排序" style="width: 100%">
                <el-option label="最后发现时间" value="last_seen" />
                <el-option label="首次发现时间" value="first_seen" />
                <el-option label="出现次数" value="occurrence_count" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <!-- 高级筛选（可折叠） -->
        <el-collapse v-model="activeCollapse" class="advanced-filter">
          <el-collapse-item title="高级筛选" name="advanced">
            <el-row :gutter="20">
              <!-- 用户ID -->
              <el-col :xs="24" :sm="12" :md="8" :lg="6">
                <el-form-item label="用户ID">
                  <el-input
                    v-model="localFilters.userId"
                    placeholder="输入用户ID"
                    clearable
                  />
                </el-form-item>
              </el-col>

              <!-- 群组ID -->
              <el-col :xs="24" :sm="12" :md="8" :lg="6">
                <el-form-item label="群组ID">
                  <el-input
                    v-model="localFilters.chatId"
                    placeholder="输入群组ID"
                    clearable
                  />
                </el-form-item>
              </el-col>

              <!-- 域名 -->
              <el-col :xs="24" :sm="12" :md="8" :lg="6">
                <el-form-item label="域名">
                  <el-input
                    v-model="localFilters.domain"
                    placeholder="输入域名"
                    clearable
                  />
                </el-form-item>
              </el-col>
            </el-row>
          </el-collapse-item>
        </el-collapse>

        <!-- 操作按钮 -->
        <el-row class="action-row">
          <el-col :span="24">
            <el-space wrap>
              <el-button type="primary" :icon="Search" @click="handleSearch">
                搜索
              </el-button>
              <el-button :icon="RefreshLeft" @click="handleReset">
                重置
              </el-button>
              <el-button v-if="hasFilters" link type="primary" @click="handleClearAll">
                清除所有筛选
              </el-button>
            </el-space>
          </el-col>
        </el-row>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { Search, RefreshLeft } from '@element-plus/icons-vue'
import { tagsApi, type Tag } from '@/api/tags'
import type { FilterConditions, ContentType, SourceType } from '@/types/adTracking'

interface Props {
  modelValue: FilterConditions
}

interface Emits {
  (e: 'update:modelValue', value: FilterConditions): void
  (e: 'search'): void
  (e: 'reset'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// ==================== 本地状态 ====================

const localFilters = ref<FilterConditions>({ ...props.modelValue })
const dateRange = ref<[string, string] | null>(null)
const sortField = ref<'first_seen' | 'last_seen' | 'occurrence_count'>('last_seen')
const activeCollapse = ref<string[]>([])

// 标签列表
const tagsList = ref<Tag[]>([])
const tagsLoading = ref(false)

// ==================== 选项配置 ====================

const contentTypeOptions = [
  { label: 'URL链接', value: 'url' },
  { label: '@账户', value: 'telegram_account' },
  { label: 't.me邀请', value: 't_me_invite' },
  { label: 't.me频道消息', value: 't_me_channel_msg' },
  { label: 't.me私聊邀请', value: 't_me_private_invite' },
  { label: 'Telegraph', value: 'telegraph' }
]

const sourceTypeOptions = [
  { label: '聊天消息', value: 'chat' },
  { label: '用户简介', value: 'user_desc' },
  { label: '用户名', value: 'username' },
  { label: '昵称', value: 'nickname' },
  { label: '群组简介', value: 'group_intro' }
]

const dateShortcuts = [
  {
    text: '今天',
    value: () => {
      const today = new Date()
      const todayStr = today.toISOString().split('T')[0]
      return [todayStr, todayStr]
    }
  },
  {
    text: '最近7天',
    value: () => {
      const end = new Date()
      const start = new Date()
      start.setTime(start.getTime() - 3600 * 1000 * 24 * 7)
      return [start.toISOString().split('T')[0], end.toISOString().split('T')[0]]
    }
  },
  {
    text: '最近30天',
    value: () => {
      const end = new Date()
      const start = new Date()
      start.setTime(start.getTime() - 3600 * 1000 * 24 * 30)
      return [start.toISOString().split('T')[0], end.toISOString().split('T')[0]]
    }
  }
]

// ==================== Computed ====================

const hasFilters = computed(() => {
  return (
    localFilters.value.contentTypes.length > 0 ||
    localFilters.value.sourceTypes.length > 0 ||
    localFilters.value.tagIds.length > 0 ||
    localFilters.value.search !== '' ||
    localFilters.value.userId !== '' ||
    localFilters.value.chatId !== '' ||
    localFilters.value.domain !== '' ||
    dateRange.value !== null
  )
})

// ==================== Methods ====================

/**
 * 获取标签列表
 */
async function fetchTags() {
  tagsLoading.value = true
  try {
    const response = await tagsApi.getList()
    if (response.err_code === 0) {
      tagsList.value = response.payload.data
    }
  } catch (error) {
    console.error('获取标签列表失败:', error)
  } finally {
    tagsLoading.value = false
  }
}

/**
 * 搜索
 */
function handleSearch() {
  // 更新日期范围
  localFilters.value.dateRange = dateRange.value

  // 更新排序
  localFilters.value.sortBy = sortField.value

  emit('update:modelValue', { ...localFilters.value })
  emit('search')
}

/**
 * 重置
 */
function handleReset() {
  localFilters.value = {
    contentTypes: [],
    sourceTypes: [],
    tagIds: [],
    dateRange: null,
    search: '',
    userId: '',
    chatId: '',
    domain: '',
    sortBy: 'last_seen',
    sortOrder: 'desc'
  }
  dateRange.value = null
  sortField.value = 'last_seen'
  activeCollapse.value = []

  emit('update:modelValue', { ...localFilters.value })
  emit('reset')
}

/**
 * 清除所有筛选
 */
function handleClearAll() {
  handleReset()
}

// ==================== 生命周期 ====================

onMounted(() => {
  fetchTags()

  // 初始化日期范围
  if (props.modelValue.dateRange) {
    dateRange.value = props.modelValue.dateRange
  }

  // 初始化排序
  if (props.modelValue.sortBy) {
    sortField.value = props.modelValue.sortBy
  }
})

// ==================== Watch ====================

// 监听props变化
watch(
  () => props.modelValue,
  (newVal) => {
    localFilters.value = { ...newVal }
    dateRange.value = newVal.dateRange
    sortField.value = newVal.sortBy
  },
  { deep: true }
)
</script>

<style scoped lang="scss">
.filter-panel {
  margin-bottom: 20px;

  :deep(.el-card__body) {
    padding: 20px;
  }

  .el-form {
    .el-form-item {
      margin-bottom: 16px;

      :deep(.el-form-item__label) {
        font-size: 13px;
        font-weight: 500;
        color: #606266;
      }
    }

    .advanced-filter {
      margin-top: 10px;
      border: none;

      :deep(.el-collapse-item__header) {
        background-color: #f5f7fa;
        padding: 0 12px;
        border-radius: 4px;
        font-size: 13px;
        font-weight: 500;
        height: 36px;
        line-height: 36px;
      }

      :deep(.el-collapse-item__wrap) {
        border: none;
      }

      :deep(.el-collapse-item__content) {
        padding: 16px 0 0 0;
      }
    }

    .action-row {
      margin-top: 16px;
      padding-top: 16px;
      border-top: 1px solid #ebeef5;
    }
  }
}

// 响应式调整
@media (max-width: 768px) {
  .filter-panel {
    :deep(.el-card__body) {
      padding: 15px;
    }

    .el-form {
      .el-form-item {
        margin-bottom: 12px;

        :deep(.el-form-item__label) {
          font-size: 12px;
        }
      }

      .action-row {
        margin-top: 12px;
        padding-top: 12px;
      }
    }
  }
}
</style>
