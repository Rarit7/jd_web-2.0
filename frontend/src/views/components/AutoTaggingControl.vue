<template>
  <div class="auto-tagging-control">
    <el-card>
      <div class="control-content">
        <!-- 统计概览 -->
        <div class="stats-overview">
          <el-row :gutter="16">
            <el-col :span="8">
              <el-statistic
                title="总标签记录"
                :value="stats.summary.total_logs"
                :precision="0"
              >
                <template #suffix>
                  <el-icon><Document /></el-icon>
                </template>
              </el-statistic>
            </el-col>
            <el-col :span="8">
              <el-statistic
                title="标记用户数"
                :value="stats.summary.unique_users"
                :precision="0"
              >
                <template #suffix>
                  <el-icon><User /></el-icon>
                </template>
              </el-statistic>
            </el-col>
            <el-col :span="8">
              <el-statistic
                title="活跃标签数"
                :value="stats.summary.unique_tags"
                :precision="0"
              >
                <template #suffix>
                  <el-icon><Files /></el-icon>
                </template>
              </el-statistic>
            </el-col>
          </el-row>
        </div>

        <!-- 运行中的任务 -->
        <div v-if="runningTasks.length > 0" class="running-tasks">
          <h4>运行中的任务</h4>
          <el-table :data="runningTasks" size="small">
            <el-table-column prop="task_id" label="任务ID" width="200" />
            <el-table-column prop="type" label="类型" width="150">
              <template #default="{ row }">
                <el-tag :type="row.type === 'daily' ? 'success' : 'warning'">
                  {{ row.type === 'daily' ? '当日数据' : '全部历史' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="getStatusType(row.status)">
                  {{ getStatusText(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="started_at" label="开始时间" width="160" />
            <el-table-column label="操作" width="100">
              <template #default="{ row }">
                <el-button
                  size="small"
                  @click="checkTaskStatus(row.task_id)"
                  :loading="row.checking"
                >
                  刷新
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>

        <!-- 统计图表 -->
        <div class="stats-charts">
          <el-row :gutter="16">
            <!-- 标签统计 -->
            <el-col :span="8">
              <div class="chart-card chart-card-scroll">
                <h4>标签统计 TOP 10</h4>
                <div v-if="stats.tag_stats.length > 0" class="tag-stats-list">
                  <div
                    v-for="(item, index) in stats.tag_stats"
                    :key="item.tag_id"
                    class="tag-stat-item"
                  >
                    <div class="tag-stat-header">
                      <span class="tag-rank-badge" :class="'rank-' + (index + 1)">{{ index + 1 }}</span>
                      <el-tag
                        :color="item.tag_color"
                        effect="dark"
                        size="small"
                        style="color: white; border: none;"
                      >
                        {{ item.tag_name }}
                      </el-tag>
                    </div>
                    <div class="tag-stat-info">
                      <span class="tag-stat-label">用户数</span>
                      <span class="tag-stat-value">{{ item.user_count }}</span>
                    </div>
                  </div>
                </div>
                <div v-else class="no-data">暂无数据</div>
              </div>
            </el-col>

            <!-- 来源统计 -->
            <el-col :span="8">
              <div class="chart-card">
                <h4>来源统计</h4>
                <div v-if="stats.source_stats.length > 0" class="source-stats">
                  <div
                    v-for="item in stats.source_stats"
                    :key="item.source_type"
                    class="stat-item"
                  >
                    <span class="stat-label">{{ getSourceTypeText(item.source_type) }}</span>
                    <span class="stat-value">{{ item.count }}</span>
                  </div>
                </div>
                <div v-else class="no-data">暂无数据</div>
              </div>
            </el-col>

            <!-- 热门关键词 -->
            <el-col :span="8">
              <div class="chart-card chart-card-scroll">
                <h4>热门关键词 TOP 10</h4>
                <div v-if="stats.keyword_stats.length > 0" class="keyword-stats">
                  <div
                    v-for="(item, index) in stats.keyword_stats.slice(0, 10)"
                    :key="item.keyword"
                    class="keyword-item"
                  >
                    <span class="keyword-rank">{{ index + 1 }}</span>
                    <span class="keyword-name">{{ item.keyword }}</span>
                    <span class="keyword-count">{{ item.count }}</span>
                  </div>
                </div>
                <div v-else class="no-data">暂无数据</div>
              </div>
            </el-col>
          </el-row>
        </div>
      </div>
    </el-card>

  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Document,
  User,
  Files,
  Loading
} from '@element-plus/icons-vue'
import { tagsApi, type AutoTagStats } from '@/api/tags'

interface Emits {
  (e: 'task-executed'): void
}

const emit = defineEmits<Emits>()

// 响应式数据
const dailyLoading = ref(false)
const historicalLoading = ref(false)
const runningTasks = ref<any[]>([])

// 统计数据
const stats = reactive<AutoTagStats>({
  summary: {
    total_logs: 0,
    unique_users: 0,
    unique_tags: 0
  },
  tag_stats: [],
  source_stats: [],
  keyword_stats: []
})

// 获取统计数据
const fetchStats = async () => {
  try {
    const response = await tagsApi.getAutoTagStats()
    if (response.err_code === 0) {
      Object.assign(stats, response.payload)
    } else {
      ElMessage.error(response.err_msg || '获取统计数据失败')
    }
  } catch (error) {
    console.error('获取统计数据失败:', error)
    ElMessage.error('获取统计数据失败')
  }
}

// 执行任务
const executeTask = async (type: 'daily' | 'historical') => {
  const loading = type === 'daily' ? dailyLoading : historicalLoading
  loading.value = true

  try {
    const response = await tagsApi.executeAutoTagging({ type })
    if (response.err_code === 0) {
      ElMessage.success(`${type === 'daily' ? '处理当日数据' : '处理全部历史数据'}任务已提交`)

      // 添加到运行任务列表
      const newTask = {
        task_id: response.payload.task_id,
        type: type,
        status: 'PENDING',
        started_at: new Date().toLocaleString(),
        checking: false
      }
      runningTasks.value.push(newTask)

      emit('task-executed')

      // 开始监控任务状态
      monitorTask(newTask)
    } else {
      ElMessage.error(response.err_msg || '任务提交失败')
    }
  } catch (error) {
    console.error('任务执行失败:', error)
    ElMessage.error('任务执行失败')
  } finally {
    loading.value = false
  }
}

// 检查任务状态
const checkTaskStatus = async (taskId: string) => {
  const task = runningTasks.value.find(t => t.task_id === taskId)
  if (!task) return

  task.checking = true
  try {
    const response = await tagsApi.getTaskStatus(taskId)
    if (response.err_code === 0) {
      task.status = response.payload.status

      // 如果任务完成，从运行列表中移除
      if (['SUCCESS', 'FAILURE', 'REVOKED'].includes(task.status)) {
        const index = runningTasks.value.findIndex(t => t.task_id === taskId)
        if (index > -1) {
          runningTasks.value.splice(index, 1)
        }

        if (task.status === 'SUCCESS') {
          ElMessage.success(`任务 ${taskId} 执行成功`)
          fetchStats() // 刷新统计数据
        } else {
          ElMessage.error(`任务 ${taskId} 执行失败`)
        }
      }
    }
  } catch (error) {
    console.error('检查任务状态失败:', error)
  } finally {
    task.checking = false
  }
}

// 监控任务
const monitorTask = (task: any) => {
  const interval = setInterval(() => {
    checkTaskStatus(task.task_id).then(() => {
      // 如果任务不在运行列表中，清除定时器
      if (!runningTasks.value.find(t => t.task_id === task.task_id)) {
        clearInterval(interval)
      }
    })
  }, 5000) // 每5秒检查一次

  // 最多监控5分钟
  setTimeout(() => {
    clearInterval(interval)
  }, 300000)
}

// 获取状态类型
const getStatusType = (status: string) => {
  switch (status) {
    case 'SUCCESS':
      return 'success'
    case 'FAILURE':
      return 'danger'
    case 'PENDING':
      return 'warning'
    case 'RUNNING':
      return 'primary'
    default:
      return 'info'
  }
}

// 获取状态文本
const getStatusText = (status: string) => {
  switch (status) {
    case 'SUCCESS':
      return '成功'
    case 'FAILURE':
      return '失败'
    case 'PENDING':
      return '等待中'
    case 'RUNNING':
      return '运行中'
    case 'REVOKED':
      return '已取消'
    default:
      return status
  }
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

// 页面加载时获取数据
onMounted(() => {
  fetchStats()
})
</script>

<style scoped>
.auto-tagging-control {
  width: 100%;
}

.control-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.stats-overview {
  padding: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 8px;
  color: white;
}

.stats-overview :deep(.el-statistic__head) {
  color: rgba(255, 255, 255, 0.8);
}

.stats-overview :deep(.el-statistic__content) {
  color: white;
}

.running-tasks {
  margin-top: 20px;
}

.running-tasks h4 {
  margin: 0 0 16px 0;
  color: #303133;
}

.stats-charts {
  margin-top: 20px;
}

.chart-card {
  padding: 20px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  height: 280px;
  display: flex;
  flex-direction: column;
}

.chart-card-scroll {
  overflow: hidden;
}

.chart-card h4 {
  margin: 0 0 16px 0;
  color: #303133;
  font-size: 14px;
  font-weight: 600;
}

.source-stats {
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex: 1;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: #f5f7fa;
  border-radius: 4px;
}

.stat-label {
  color: #606266;
  font-size: 13px;
}

.stat-value {
  color: #303133;
  font-weight: 600;
}

.keyword-stats {
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex: 1;
  overflow-y: auto;
}

.keyword-item {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  background: #f5f7fa;
  border-radius: 4px;
  font-size: 13px;
}

.keyword-rank {
  width: 24px;
  height: 24px;
  background: #409eff;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  margin-right: 12px;
}

.keyword-name {
  flex-grow: 1;
  color: #303133;
}

.keyword-count {
  color: #909399;
  font-weight: 600;
}

.no-data {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100px;
  color: #909399;
  font-size: 14px;
}

.tag-stats-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex: 1;
  overflow-y: auto;
}

.tag-stat-item {
  padding: 8px 12px;
  background: #f5f7fa;
  border-radius: 6px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  transition: all 0.3s;
}

.tag-stat-item:hover {
  background: #ecf5ff;
  transform: translateX(2px);
}

.tag-stat-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.tag-rank-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  font-weight: 600;
  font-size: 12px;
  flex-shrink: 0;
}

.tag-rank-badge.rank-1 {
  background: linear-gradient(135deg, #ffd700 0%, #ffed4e 100%);
  color: #8b4513;
}

.tag-rank-badge.rank-2 {
  background: linear-gradient(135deg, #c0c0c0 0%, #e8e8e8 100%);
  color: #5a5a5a;
}

.tag-rank-badge.rank-3 {
  background: linear-gradient(135deg, #cd7f32 0%, #e6a85c 100%);
  color: #4a2c0f;
}

.tag-rank-badge:not(.rank-1):not(.rank-2):not(.rank-3) {
  background: #e4e7ed;
  color: #606266;
}

.tag-stat-info {
  display: flex;
  align-items: center;
  gap: 6px;
}

.tag-stat-label {
  font-size: 12px;
  color: #909399;
}

.tag-stat-value {
  font-size: 16px;
  font-weight: 600;
  color: #409eff;
}
</style>