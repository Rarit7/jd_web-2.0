<template>
  <div class="auto-tagging">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>自动标签</span>
          <el-button
            type="success"
            :icon="CaretRight"
            @click="showExecuteDialog = true"
          >
            执行自动标签任务
          </el-button>
        </div>
      </template>

      <div class="stats-section">
        <!-- 统计概览 -->
        <AutoTaggingControl @task-executed="handleTaskExecuted" />

        <!-- 自动标签日志 -->
        <div class="logs-section">
          <AutoTaggingLogs @view-detail="handleViewLogDetail" />
        </div>
      </div>
    </el-card>

    <!-- 执行任务对话框 -->
    <el-dialog v-model="showExecuteDialog" title="执行自动标签任务" width="500px">
      <el-form :model="executeForm" label-width="120px">
        <el-form-item label="任务类型">
          <el-radio-group v-model="executeForm.type">
            <el-radio value="daily">处理当日数据</el-radio>
            <el-radio value="historical">处理全部历史数据</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item>
          <div class="task-description">
            <div v-if="executeForm.type === 'daily'">
              处理当日0:00到当前时刻的新增数据,为匹配关键词的用户自动添加标签。
            </div>
            <div v-else>
              对所有历史聊天记录和用户信息进行关键词匹配。可能需要较长时间。
            </div>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showExecuteDialog = false">取消</el-button>
        <el-button type="primary" @click="handleExecuteTask" :loading="executeLoading">
          执行任务
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { CaretRight } from '@element-plus/icons-vue'
import { tagsApi } from '@/api/tags'
import AutoTaggingControl from '@/views/components/AutoTaggingControl.vue'
import AutoTaggingLogs from '@/views/components/AutoTaggingLogs.vue'

// 响应式数据
const showExecuteDialog = ref(false)
const executeLoading = ref(false)

// 执行任务表单
const executeForm = reactive({
  type: 'daily' as 'daily' | 'historical'
})

// 查看日志详情
const handleViewLogDetail = (log: any) => {
  // TODO: 实现日志详情抽屉
  console.log('View log detail:', log)
}

// 执行自动标签任务
const handleExecuteTask = async () => {
  executeLoading.value = true
  try {
    const response = await tagsApi.executeAutoTagging({ type: executeForm.type })
    if (response.err_code === 0) {
      const payload = response.payload
      if (payload.status === 'WAITING') {
        ElMessage.info(`任务已加入等待队列，队列位置：${payload.queue_position || 1}`)
      } else if (payload.status === 'SUCCESS') {
        ElMessage.success('任务执行成功')
      } else {
        ElMessage.success('任务已提交')
      }
      showExecuteDialog.value = false
    } else {
      ElMessage.error(response.err_msg || '任务提交失败')
    }
  } catch (error) {
    console.error('任务执行失败:', error)
    // 错误消息已经在axios拦截器中显示
  } finally {
    executeLoading.value = false
  }
}

// 任务执行处理
const handleTaskExecuted = () => {
  ElMessage.success('任务已提交')
}
</script>

<style scoped>
.auto-tagging {
  height: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stats-section {
  display: flex;
  flex-direction: column;
  gap: 24px;
  width: 100%;
}

.logs-section {
  margin-top: 24px;
  width: 100%;
}

.task-description {
  padding: 12px;
  background-color: #f5f7fa;
  border-radius: 4px;
  color: #606266;
  font-size: 14px;
  line-height: 1.5;
}
</style>
