<template>
  <div class="auto-tagging-logs">
    <!-- 过滤器 -->
    <div class="filters">
      <div class="filter-row">
        <el-select
          v-model="filters.tag_id"
          placeholder="选择标签"
          clearable
          @change="handleTagChange"
          style="width: 300px;"
        >
          <el-option
            v-for="tag in tags"
            :key="tag.id"
            :label="tag.name"
            :value="tag.id"
          >
            <div style="display: flex; align-items: center;">
              <el-tag :color="tag.color" effect="dark" size="small" style="margin-right: 8px; color: white; border: none;">
                {{ tag.name }}
              </el-tag>
            </div>
          </el-option>
        </el-select>

        <el-select
          v-model="filters.keywords"
          placeholder="选择关键词"
          multiple
          clearable
          filterable
          :disabled="!filters.tag_id"
          :loading="keywordsLoading"
          @change="fetchData"
          style="width: 400px; margin-left: 12px;"
        >
          <template #prefix>
            <span v-if="filters.keywords && filters.keywords.length > 0" style="font-size: 12px; color: #909399;">
              已选 {{ filters.keywords.length }} 个
            </span>
          </template>
          <el-option
            v-for="keyword in availableKeywords"
            :key="keyword.id"
            :label="keyword.keyword"
            :value="keyword.keyword"
          >
            <span>{{ keyword.keyword }}</span>
          </el-option>
        </el-select>
      </div>
    </div>

    <!-- 日志表格 -->
    <div v-loading="loading" class="table-container">
      <el-table :data="tableData" style="width: 100%" stripe>
        <el-table-column label="标签" width="150">
          <template #default="{ row }">
            <el-tag
              v-if="getTagById(row.tag_id)"
              :color="getTagById(row.tag_id)?.color"
              effect="dark"
              size="small"
              style="color: white; border: none;"
            >
              {{ getTagById(row.tag_id)?.name }}
            </el-tag>
            <span v-else>未知标签</span>
          </template>
        </el-table-column>

        <el-table-column label="用户昵称" width="200">
          <template #default="{ row }">
            <span class="user-nickname-link" @click="handleOpenUserDrawer(row)">
              {{ getUserNickname(row) }}
            </span>
          </template>
        </el-table-column>

        <el-table-column prop="keyword" label="触发关键词" width="150">
          <template #default="{ row }">
            <el-tag type="warning" effect="light">{{ row.keyword }}</el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="source_type" label="来源类型" width="120">
          <template #default="{ row }">
            <el-tag :type="getSourceTypeTagType(row.source_type)" size="small">
              {{ getSourceTypeText(row.source_type) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="详细内容" min-width="300">
          <template #default="{ row }">
            <div class="detail-content">
              {{ getDetailContent(row) }}
            </div>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="250" fixed="right">
          <template #default="{ row }">
            <div class="action-buttons">
              <el-button
                type="primary"
                size="small"
                @click="handleViewDetail(row)"
              >
                详情
              </el-button>
              <el-button
                v-if="row.source_type === 'chat'"
                type="info"
                size="small"
                @click="handleViewContext(row)"
              >
                查看上下文
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </div>

    <!-- 详情对话框 -->
    <el-dialog v-model="showDetailDialog" title="日志详情" width="700px">
      <div v-if="selectedLog" class="log-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="用户ID">{{ selectedLog.tg_user_id }}</el-descriptions-item>
          <el-descriptions-item label="标签">
            <el-tag
              v-if="getTagById(selectedLog.tag_id)"
              :color="getTagById(selectedLog.tag_id)?.color"
              effect="dark"
              size="small"
              style="color: white; border: none;"
            >
              {{ getTagById(selectedLog.tag_id)?.name }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="触发关键词">
            <el-tag type="warning">{{ selectedLog.keyword }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="来源类型">
            <el-tag :type="getSourceTypeTagType(selectedLog.source_type)">
              {{ getSourceTypeText(selectedLog.source_type) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="创建时间" :span="2">
            {{ formatDate(selectedLog.created_at) }}
          </el-descriptions-item>
        </el-descriptions>

        <!-- 用户详细信息 -->
        <div v-if="selectedLog.detail_info" class="detail-info-section">
          <h4>用户信息</h4>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="用户昵称">
              {{ selectedLog.detail_info.user_nickname || '(无)' }}
            </el-descriptions-item>
            <el-descriptions-item label="用户名">
              {{ selectedLog.detail_info.user_username || '(无)' }}
            </el-descriptions-item>
          </el-descriptions>

          <!-- 聊天消息特有信息 -->
          <div v-if="selectedLog.source_type === 'chat'" class="source-specific-info">
            <h4>聊天消息详情</h4>
            <el-descriptions :column="2" border>
              <el-descriptions-item label="群组ID">
                {{ selectedLog.detail_info.chat_id || '(无)' }}
              </el-descriptions-item>
              <el-descriptions-item label="群组名称">
                {{ selectedLog.detail_info.chat_title || '(无)' }}
              </el-descriptions-item>
              <el-descriptions-item label="消息ID">
                {{ selectedLog.detail_info.message_id || '(无)' }}
              </el-descriptions-item>
              <el-descriptions-item label="消息时间">
                {{ selectedLog.detail_info.message_date ? formatDate(selectedLog.detail_info.message_date) : '(无)' }}
              </el-descriptions-item>
              <el-descriptions-item label="消息内容" :span="2">
                <div class="message-content">
                  <HighlightText
                    v-if="selectedLog.detail_info.message_text"
                    :text="selectedLog.detail_info.message_text"
                    :keywords="selectedLog.keyword"
                  />
                  <span v-else>(无)</span>
                </div>
              </el-descriptions-item>
            </el-descriptions>
          </div>

          <!-- 昵称特有信息 -->
          <div v-if="selectedLog.source_type === 'nickname'" class="source-specific-info">
            <h4>昵称详情</h4>
            <el-descriptions :column="1" border>
              <el-descriptions-item label="昵称">
                <HighlightText
                  v-if="selectedLog.detail_info.nickname || selectedLog.detail_info.new_nickname || selectedLog.detail_info.old_nickname"
                  :text="selectedLog.detail_info.nickname || selectedLog.detail_info.new_nickname || selectedLog.detail_info.old_nickname || ''"
                  :keywords="selectedLog.keyword"
                />
                <span v-else>(无)</span>
              </el-descriptions-item>
            </el-descriptions>
          </div>

          <!-- 描述特有信息 -->
          <div v-if="selectedLog.source_type === 'desc'" class="source-specific-info">
            <h4>描述详情</h4>
            <el-descriptions :column="1" border>
              <el-descriptions-item label="描述">
                <div class="desc-content">
                  <HighlightText
                    v-if="selectedLog.detail_info.desc || selectedLog.detail_info.new_desc || selectedLog.detail_info.old_desc"
                    :text="selectedLog.detail_info.desc || selectedLog.detail_info.new_desc || selectedLog.detail_info.old_desc || ''"
                    :keywords="selectedLog.keyword"
                  />
                  <span v-else>(无)</span>
                </div>
              </el-descriptions-item>
            </el-descriptions>
          </div>
        </div>
      </div>
    </el-dialog>

    <!-- 用户详情抽屉 -->
    <UserDetailDrawer
      v-model:visible="showUserDrawer"
      :userId="selectedUserId"
      @navigate-to-user-messages="handleNavigateToUserMessages"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { tagsApi, type AutoTagLog, type Tag } from '@/api/tags'
import { chatHistoryApi } from '@/api/chat-history'
import HighlightText from '@/components/HighlightText.vue'
import UserDetailDrawer from '@/components/UserDetailDrawer.vue'

interface Emits {
  (e: 'view-detail', log: AutoTagLog): void
}

const emit = defineEmits<Emits>()
const router = useRouter()

// 响应式数据
const loading = ref(false)
const tableData = ref<AutoTagLog[]>([])
const tags = ref<Tag[]>([])
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const showDetailDialog = ref(false)
const selectedLog = ref<AutoTagLog>()

// 用户详情抽屉相关
const showUserDrawer = ref(false)
const selectedUserId = ref<string>()

// 关键词相关
const keywordsLoading = ref(false)
const availableKeywords = ref<Array<{ id: number; keyword: string }>>([])

// 过滤器
const filters = reactive({
  tag_id: undefined as number | undefined,
  keywords: [] as string[]
})

// 获取标签列表
const fetchTags = async () => {
  try {
    const response = await tagsApi.getList()
    if (response.err_code === 0) {
      tags.value = response.payload.data
    }
  } catch (error) {
    console.error('获取标签列表失败:', error)
  }
}

// 获取指定标签的所有关键词
const fetchKeywords = async (tagId: number) => {
  keywordsLoading.value = true
  try {
    const response = await tagsApi.getAllTagKeywords(tagId)
    if (response.err_code === 0) {
      availableKeywords.value = response.payload.data
    } else {
      ElMessage.error(response.err_msg || '获取关键词失败')
      availableKeywords.value = []
    }
  } catch (error) {
    console.error('获取关键词失败:', error)
    ElMessage.error('获取关键词失败')
    availableKeywords.value = []
  } finally {
    keywordsLoading.value = false
  }
}

// 处理标签变更
const handleTagChange = (tagId: number | undefined) => {
  // 清空关键词选择
  filters.keywords = []
  availableKeywords.value = []

  // 如果选择了标签，获取该标签的关键词
  if (tagId) {
    fetchKeywords(tagId)
  }

  // 刷新数据
  fetchData()
}

// 获取日志数据
const fetchData = async () => {
  loading.value = true
  try {
    const params: any = {
      page: currentPage.value,
      page_size: pageSize.value,
      tag_id: filters.tag_id
    }

    // 如果选择了关键词，将数组转换为逗号分隔的字符串
    if (filters.keywords && filters.keywords.length > 0) {
      params.keywords = filters.keywords.join(',')
    }

    // 清理空值
    Object.keys(params).forEach(key => {
      if (params[key] === '' || params[key] === undefined) {
        delete params[key]
      }
    })

    const response = await tagsApi.getAutoTagLogs(params)
    if (response.err_code === 0) {
      tableData.value = response.payload.data
      total.value = response.payload.total
    } else {
      ElMessage.error(response.err_msg || '获取日志失败')
    }
  } catch (error) {
    console.error('获取日志失败:', error)
    ElMessage.error('获取日志失败')
  } finally {
    loading.value = false
  }
}

// 分页大小变更
const handleSizeChange = (newSize: number) => {
  pageSize.value = newSize
  currentPage.value = 1
  fetchData()
}

// 当前页变更
const handleCurrentChange = (newPage: number) => {
  currentPage.value = newPage
  fetchData()
}

// 查看详情
const handleViewDetail = (row: AutoTagLog) => {
  selectedLog.value = row
  showDetailDialog.value = true
  // 发出事件给父组件
  emit('view-detail', row)
}

// 打开用户详情抽屉
const handleOpenUserDrawer = (row: AutoTagLog) => {
  selectedUserId.value = row.tg_user_id
  showUserDrawer.value = true
}

// 处理从用户详情抽屉导航到群组
const handleNavigateToUserMessages = (data: { groupId: string, userId: string }) => {
  showUserDrawer.value = false
  router.push({
    path: '/chat-history',
    query: {
      group_id: data.groupId,
      user_id: data.userId,
      search_type: 'user_id'
    }
  })
}

// 查看上下文（仅聊天消息）- 跨页面跳转到ChatHistory并定位消息
const handleViewContext = async (row: AutoTagLog) => {
  if (row.source_type !== 'chat' || !row.detail_info || !row.detail_info.chat_id) {
    ElMessage.warning('无法定位消息上下文')
    return
  }

  try {
    const chatId = row.detail_info.chat_id
    const messageId = parseInt(row.source_id)

    // 调用后端API查找消息所在的页数
    const response = await chatHistoryApi.findMessagePage(chatId, messageId, 20)

    if (response.data.err_code === 0) {
      const payload = response.data.payload
      const pageNumber = payload.page_number

      // 跳转到聊天历史页面，传递必要参数
      // 使用特殊的参数格式，让ChatHistory页面知道这是一个需要定位的跳转
      await router.push({
        path: '/chat-history',
        query: {
          group_id: chatId,
          page: pageNumber.toString(),
          message_id: messageId.toString(),
          auto_scroll: 'true'  // 标记需要自动滚动到消息
        }
      })

      ElMessage.success(`正在跳转到消息上下文（第${pageNumber}页）`)
    } else {
      ElMessage.error(response.data.err_msg || '查找消息位置失败')
    }
  } catch (error) {
    console.error('查看上下文失败:', error)
    ElMessage.error('查看上下文失败')
  }
}

// 根据ID获取标签
const getTagById = (tagId: number) => {
  return tags.value.find(tag => tag.id === tagId)
}

// 获取来源类型文本
const getSourceTypeText = (sourceType: string) => {
  switch (sourceType) {
    case 'chat':
      return '聊天消息'
    case 'nickname':
      return '用户昵称'
    case 'desc':
      return '用户描述'
    default:
      return sourceType
  }
}

// 获取来源类型标签类型
const getSourceTypeTagType = (sourceType: string) => {
  switch (sourceType) {
    case 'chat':
      return 'primary'
    case 'nickname':
      return 'success'
    case 'desc':
      return 'warning'
    default:
      return 'info'
  }
}

// 格式化日期
const formatDate = (dateString: string) => {
  if (!dateString) return ''
  return new Date(dateString).toLocaleString('zh-CN')
}

// 获取用户昵称
const getUserNickname = (row: AutoTagLog) => {
  if (row.detail_info?.user_nickname) {
    return row.detail_info.user_nickname
  }
  if (row.detail_info?.user_username) {
    return row.detail_info.user_username
  }
  return `User_${row.tg_user_id}`
}

// 获取详细内容
const getDetailContent = (row: AutoTagLog) => {
  if (!row.detail_info) {
    return '无详细信息'
  }

  const info = row.detail_info

  switch (row.source_type) {
    case 'chat': {
      const text = info.message_text || ''
      const maxLength = 100
      return text.length > maxLength ? text.substring(0, maxLength) + '...' : text
    }
    case 'nickname': {
      const nick = info.nickname || info.new_nickname || info.old_nickname || '(无)'
      return nick
    }
    case 'desc': {
      const desc = info.desc || info.new_desc || info.old_desc || ''
      const maxLength = 100
      return desc.length > maxLength ? desc.substring(0, maxLength) + '...' : desc
    }
    default:
      return '未知类型'
  }
}

// 页面加载时获取数据
onMounted(() => {
  fetchTags()
  fetchData()
})
</script>

<style scoped>
.auto-tagging-logs {
  height: 100%;
  width: 100%;
}

.filters {
  margin-bottom: 20px;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 8px;
}

.filter-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}

.table-container {
  background: white;
  border-radius: 8px;
  min-height: 400px;
  width: 100%;
}

.pagination {
  display: flex;
  justify-content: center;
  margin-top: 20px;
  padding: 20px 0;
}

.log-detail {
  padding: 20px 0;
}

.detail-content {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
}

.detail-info-section {
  margin-top: 24px;
}

.detail-info-section h4 {
  margin: 16px 0 12px 0;
  color: #303133;
  font-size: 14px;
  font-weight: 600;
  padding-left: 8px;
  border-left: 3px solid #409eff;
}

.source-specific-info {
  margin-top: 16px;
}

.message-content,
.desc-content {
  max-height: 200px;
  overflow-y: auto;
  padding: 8px;
  background: #f5f7fa;
  border-radius: 4px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}

.action-buttons {
  display: flex;
  gap: 8px;
  justify-content: flex-start;
  flex-wrap: nowrap;
  align-items: center;
}

.user-nickname-link {
  color: #1890ff;
  cursor: pointer;
  transition: color 0.3s;
  text-decoration: underline;

  &:hover {
    color: #40a9ff;
  }
}
</style>