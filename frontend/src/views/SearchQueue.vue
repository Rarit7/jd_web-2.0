<template>
  <div class="search-queue">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>抓取进度管理</span>
          <div class="header-actions">
            <el-button type="primary" size="small">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
            <el-button type="success" size="small">
              <el-icon><Plus /></el-icon>
              新增任务
            </el-button>
          </div>
        </div>
      </template>

      
      <div class="table-container">
        <el-table :data="queueList" stripe style="width: 100%">
          <el-table-column prop="id" label="队列ID" width="100" />
          <el-table-column prop="description" label="任务描述" min-width="300" show-overflow-tooltip />
          <el-table-column prop="result" label="执行结果" min-width="200" show-overflow-tooltip />
          <el-table-column prop="status" label="状态" width="120">
            <template #default="{ row }">
              <el-tag :type="getStatusType(row.status)">
                {{ getStatusLabel(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" width="180">
            <template #default="{ row }">
              {{ formatUTCToLocal(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column prop="updated_at" label="更新时间" width="180">
            <template #default="{ row }">
              {{ formatUTCToLocal(row.updated_at) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="140" fixed="right">
            <template #default="{ row }">
              <el-button 
                v-if="row.status !== 2" 
                size="small" 
                type="success"
                @click="markAsCompleted(row)"
              >
                标记为完成
              </el-button>
              <span v-else class="completed-text">已完成</span>
            </template>
          </el-table-column>
        </el-table>
        
        <div class="pagination-container">
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
    </el-card>

    <!-- 日志监控卡片 -->
    <el-card style="margin-top: 20px;">
      <template #header>
        <div class="card-header">
          <span>系统日志监控</span>
          <div class="header-actions">
            <el-button type="primary" size="small" @click="refreshLogs" :loading="logsLoading">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </div>
        </div>
      </template>

      <el-tabs v-model="selectedLog" @tab-click="handleTabClick">
        <el-tab-pane
          v-for="log in logFiles"
          :key="log.value"
          :label="log.label"
          :name="log.value"
        >
          <div class="log-container">
            <div v-if="logsLoading" class="loading-container">
              <el-icon class="is-loading"><Loading /></el-icon>
              <span>加载日志中...</span>
            </div>
            <div v-else-if="logContent" class="log-content">
              <div class="log-lines" v-html="formatLogContent(logContent)"></div>
            </div>
            <div v-else class="empty-log">
              <el-empty description="暂无日志数据" />
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { Refresh, Plus, Loading } from '@element-plus/icons-vue'
import axios from 'axios'
import { formatUTCToLocal } from '@/utils/date'

const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)

// 日志相关状态
const selectedLog = ref('celery_out.txt')
const logContent = ref('')
const logsLoading = ref(false)

const logFiles = ref([
  { label: 'Celery Worker 日志', value: 'celery_out.txt' },
  { label: 'Celery Telegram 日志', value: 'celery_telegram_out.txt' },
  { label: 'Celery Beat 日志', value: 'celery_beat.txt' },
  { label: 'Flask 后端日志', value: 'flask_out.txt' },
  { label: '前端开发日志', value: 'frontend_out.txt' }
])

const queueList = ref([])

const getStatusType = (status: number) => {
  const statusMap: Record<number, string> = {
    0: 'info',     // 待处理
    1: 'warning',  // 处理中
    2: 'success'   // 已处理
  }
  return statusMap[status] || 'info'
}

const getStatusLabel = (status: number) => {
  const statusMap: Record<number, string> = {
    0: '待处理',
    1: '处理中', 
    2: '已处理'
  }
  return statusMap[status] || '未知'
}

const handleSizeChange = (size: number) => {
  pageSize.value = size
  loadData()
}

const handleCurrentChange = (page: number) => {
  currentPage.value = page
  loadData()
}

const loadData = async () => {
  try {
    const response = await axios.get(`/api/job-queue/list`, {
      params: {
        page: currentPage.value,
        page_size: pageSize.value
      }
    })
    
    if (response.data.err_code === 0) {
      queueList.value = response.data.payload.items
      total.value = response.data.payload.pagination.total
    } else {
      console.error('获取任务队列数据失败:', response.data.err_msg)
      queueList.value = []
      total.value = 0
    }
  } catch (error) {
    console.error('获取任务队列数据失败:', error)
    queueList.value = []
    total.value = 0
  }
}

// 标记为完成
const markAsCompleted = async (row: any) => {
  try {
    const response = await axios.put(`/api/job-queue/${row.id}/complete`)
    
    if (response.data.err_code === 0) {
      // 更新本地状态
      row.status = 2
      row.updated_at = response.data.payload.updated_at
      console.log(`标记任务 ${row.id} 为完成`)
    } else {
      console.error('标记任务完成失败:', response.data.err_msg)
    }
  } catch (error) {
    console.error('标记任务完成失败:', error)
  }
}

// 获取日志内容
const fetchLogs = async () => {
  if (!selectedLog.value) return
  
  logsLoading.value = true
  try {
    const response = await axios.get(`/api/system/logs/${selectedLog.value}`)
    if (response.data.err_code === 0) {
      logContent.value = response.data.payload.content
    } else {
      logContent.value = `获取日志失败: ${response.data.err_msg}`
    }
  } catch (error) {
    logContent.value = '获取日志失败: 网络错误'
    console.error('获取日志失败:', error)
  } finally {
    logsLoading.value = false
  }
}

// 刷新日志
const refreshLogs = () => {
  fetchLogs()
}

// 格式化日志内容，添加颜色高亮
const formatLogContent = (content: string) => {
  if (!content) return ''
  
  // 按行分割
  const lines = content.split('\n')
  
  return lines.map(line => {
    // 转义HTML特殊字符
    const escapedLine = line
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;')
    
    // 检测不同日志级别并添加颜色类
    if (/\b(ERROR|error|Error)\b/.test(line)) {
      return `<div class="log-line log-error">${escapedLine}</div>`
    } else if (/\b(WARN|WARNING|warn|warning|Warn|Warning)\b/.test(line)) {
      return `<div class="log-line log-warn">${escapedLine}</div>`
    } else if (/\b(INFO|info|Info)\b/.test(line)) {
      return `<div class="log-line log-info">${escapedLine}</div>`
    } else if (/\b(DEBUG|debug|Debug)\b/.test(line)) {
      return `<div class="log-line log-debug">${escapedLine}</div>`
    } else {
      return `<div class="log-line">${escapedLine}</div>`
    }
  }).join('')
}

// 处理标签页切换
const handleTabClick = (tab: any) => {
  selectedLog.value = tab.name
  fetchLogs()
}

// 监听日志文件切换
watch(selectedLog, () => {
  if (selectedLog.value) {
    fetchLogs()
  }
})

onMounted(() => {
  loadData()
  fetchLogs()
})
</script>

<style lang="scss" scoped>
.search-queue {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;

    .header-actions {
      .el-button {
        margin-left: 8px;
      }
    }
  }


  .table-container {
    .completed-text {
      color: var(--el-color-success);
      font-weight: 500;
      font-size: 13px;
    }

    .pagination-container {
      margin-top: 20px;
      text-align: right;
    }
  }

  .log-container {
    min-height: 400px;
    max-height: 500px;

    .loading-container {
      display: flex;
      align-items: center;
      justify-content: center;
      height: 200px;
      color: var(--el-text-color-secondary);

      .el-icon {
        margin-right: 8px;
        font-size: 18px;
      }
    }

    .log-content {
      background-color: #1e1e1e;
      border-radius: 6px;
      overflow: auto;
      max-height: 460px;

      .log-lines {
        margin: 0;
        padding: 16px;
        font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
        font-size: 12px;
        line-height: 1.4;

        :deep(.log-line) {
          margin: 0;
          white-space: pre-wrap;
          word-wrap: break-word;
          color: #d4d4d4 !important;
          font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
          font-size: 12px;
          line-height: 1.4;

          &.log-error {
            color: #ff7875 !important;
            background-color: rgba(255, 77, 79, 0.15) !important;
            padding: 2px 8px;
            border-left: 3px solid #ff7875;
            margin: 1px 0;
            border-radius: 2px;
          }

          &.log-warn {
            color: #ffa940 !important;
            background-color: rgba(255, 169, 64, 0.15) !important;
            padding: 2px 8px;
            border-left: 3px solid #ffa940;
            margin: 1px 0;
            border-radius: 2px;
          }

          &.log-info {
            color: #d4d4d4 !important;
          }

          &.log-debug {
            color: #bfbfbf !important;
          }
        }
      }

      pre {
        margin: 0;
        padding: 16px;
        color: #d4d4d4;
        font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
        font-size: 12px;
        line-height: 1.4;
        white-space: pre-wrap;
        word-wrap: break-word;
      }
    }

    .empty-log {
      display: flex;
      align-items: center;
      justify-content: center;
      height: 200px;
    }
  }
}
</style>
