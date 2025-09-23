<template>
  <div class="auto-tagging-logs">
    <!-- 过滤器 -->
    <div class="filters">
      <el-row :gutter="16">
        <el-col :span="6">
          <el-select
            v-model="filters.tag_id"
            placeholder="选择标签"
            clearable
            @change="fetchData"
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
        </el-col>
        <el-col :span="6">
          <el-input
            v-model="filters.user_id"
            placeholder="用户ID"
            clearable
            @input="handleUserIdFilter"
          />
        </el-col>
        <el-col :span="6">
          <el-select
            v-model="filters.source_type"
            placeholder="来源类型"
            clearable
            @change="fetchData"
          >
            <el-option label="聊天消息" value="chat" />
            <el-option label="用户昵称" value="nickname" />
            <el-option label="用户描述" value="desc" />
          </el-select>
        </el-col>
        <el-col :span="6">
          <el-button @click="handleReset" :icon="Refresh">重置</el-button>
          <el-button type="primary" @click="fetchData" :icon="Search">搜索</el-button>
        </el-col>
      </el-row>
    </div>

    <!-- 日志表格 -->
    <div v-loading="loading" class="table-container">
      <el-table :data="tableData" style="width: 100%" stripe>
        <el-table-column prop="id" label="ID" width="80" />

        <el-table-column label="标签" width="120">
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

        <el-table-column prop="tg_user_id" label="用户ID" width="100" />

        <el-table-column prop="keyword" label="触发关键词" width="120">
          <template #default="{ row }">
            <el-tag type="warning" effect="light">{{ row.keyword }}</el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="source_type" label="来源类型" width="100">
          <template #default="{ row }">
            <el-tag :type="getSourceTypeTagType(row.source_type)" size="small">
              {{ getSourceTypeText(row.source_type) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="source_id" label="来源ID" width="120" />

        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>

        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              size="small"
              @click="handleViewDetail(row)"
            >
              详情
            </el-button>
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
    <el-dialog v-model="showDetailDialog" title="日志详情" width="600px">
      <div v-if="selectedLog" class="log-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="ID">{{ selectedLog.id }}</el-descriptions-item>
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
          <el-descriptions-item label="关键词">
            <el-tag type="warning">{{ selectedLog.keyword }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="来源类型">
            <el-tag :type="getSourceTypeTagType(selectedLog.source_type)">
              {{ getSourceTypeText(selectedLog.source_type) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="来源ID">{{ selectedLog.source_id }}</el-descriptions-item>
          <el-descriptions-item label="创建时间" :span="2">
            {{ formatDate(selectedLog.created_at) }}
          </el-descriptions-item>
        </el-descriptions>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Refresh } from '@element-plus/icons-vue'
import { tagsApi, type AutoTagLog, type Tag } from '@/api/tags'

// 响应式数据
const loading = ref(false)
const tableData = ref<AutoTagLog[]>([])
const tags = ref<Tag[]>([])
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const showDetailDialog = ref(false)
const selectedLog = ref<AutoTagLog>()

// 过滤器
const filters = reactive({
  tag_id: undefined as number | undefined,
  user_id: '',
  source_type: ''
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

// 获取日志数据
const fetchData = async () => {
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      page_size: pageSize.value,
      ...filters
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

// 用户ID过滤器处理
const handleUserIdFilter = () => {
  // 可以添加防抖逻辑
  setTimeout(() => {
    fetchData()
  }, 500)
}

// 重置过滤器
const handleReset = () => {
  filters.tag_id = undefined
  filters.user_id = ''
  filters.source_type = ''
  currentPage.value = 1
  fetchData()
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

// 页面加载时获取数据
onMounted(() => {
  fetchTags()
  fetchData()
})
</script>

<style scoped>
.auto-tagging-logs {
  height: 100%;
}

.filters {
  margin-bottom: 20px;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 8px;
}

.table-container {
  background: white;
  border-radius: 8px;
  min-height: 400px;
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
</style>