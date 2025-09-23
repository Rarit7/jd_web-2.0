<template>
  <div class="tag-keyword-mapping">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>标签关键词映射管理</span>
          <div class="header-actions">
            <el-button
              type="success"
              :icon="CaretRight"
              @click="showExecuteDialog = true"
            >
              执行自动标签任务
            </el-button>
            <el-button
              type="primary"
              :icon="Plus"
              @click="showAddDialog = true"
            >
              添加关键词映射
            </el-button>
          </div>
        </div>
      </template>

      <!-- 标签选择器 -->
      <div class="tag-selector">
        <el-select
          v-model="selectedTagId"
          placeholder="选择标签查看关键词"
          style="width: 300px"
          @change="handleTagChange"
          clearable
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
      </div>

      <!-- 关键词列表 -->
      <div v-if="selectedTagId" class="keywords-section">
        <div class="section-header">
          <h3>关键词列表</h3>
          <div class="section-actions">
            <el-button
              type="primary"
              size="small"
              :icon="Plus"
              @click="showKeywordDialog = true"
            >
              添加关键词
            </el-button>
            <el-button
              type="warning"
              size="small"
              :icon="DocumentAdd"
              @click="showBatchDialog = true"
            >
              批量导入
            </el-button>
          </div>
        </div>

        <KeywordList
          :tag-id="selectedTagId"
          :key="selectedTagId"
          @refresh="fetchTags"
        />
      </div>

      <!-- 控制面板 -->
      <div class="control-panel">
        <AutoTaggingControl @task-executed="handleTaskExecuted" />
      </div>
    </el-card>

    <!-- 添加关键词映射对话框 -->
    <el-dialog v-model="showAddDialog" title="添加关键词映射" width="500px">
      <KeywordForm
        @success="handleAddSuccess"
        @cancel="showAddDialog = false"
      />
    </el-dialog>

    <!-- 添加关键词对话框 -->
    <el-dialog v-model="showKeywordDialog" title="添加关键词" width="500px">
      <KeywordForm
        :tag-id="selectedTagId"
        @success="handleKeywordSuccess"
        @cancel="showKeywordDialog = false"
      />
    </el-dialog>

    <!-- 批量导入对话框 -->
    <el-dialog v-model="showBatchDialog" title="批量导入关键词" width="600px">
      <el-form :model="batchForm" label-width="120px">
        <el-form-item label="关键词列表">
          <el-input
            v-model="batchForm.keywords"
            type="textarea"
            :rows="8"
            placeholder="请输入关键词，每行一个，例如：&#10;济南&#10;菏泽&#10;日照&#10;烟台"
          />
          <div class="form-tip">每行输入一个关键词，支持中英文</div>
        </el-form-item>
        <el-form-item label="自动关注">
          <el-switch
            v-model="batchForm.autoFocus"
            active-text="是"
            inactive-text="否"
          />
          <div class="form-tip">开启后，匹配到关键词的用户将自动加入特别关注</div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showBatchDialog = false">取消</el-button>
        <el-button type="primary" @click="handleBatchImport" :loading="batchLoading">导入</el-button>
      </template>
    </el-dialog>

    <!-- 执行任务对话框 -->
    <el-dialog v-model="showExecuteDialog" title="执行自动标签任务" width="500px">
      <el-form :model="executeForm" label-width="120px">
        <el-form-item label="任务类型">
          <el-radio-group v-model="executeForm.type">
            <el-radio value="daily">日常任务</el-radio>
            <el-radio value="historical">历史数据处理</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item>
          <div class="task-description">
            <div v-if="executeForm.type === 'daily'">
              处理昨天的聊天记录和用户信息变更，为匹配关键词的用户自动添加标签。
            </div>
            <div v-else>
              对所有历史聊天记录和用户信息进行关键词匹配，可能需要较长时间。
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
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, CaretRight, DocumentAdd } from '@element-plus/icons-vue'
import { tagsApi, type Tag } from '@/api/tags'
import KeywordForm from '@/views/components/KeywordForm.vue'
import KeywordList from '@/views/components/KeywordList.vue'
import AutoTaggingControl from '@/views/components/AutoTaggingControl.vue'

// 响应式数据
const tags = ref<Tag[]>([])
const selectedTagId = ref<number>()
const showAddDialog = ref(false)
const showKeywordDialog = ref(false)
const showBatchDialog = ref(false)
const showExecuteDialog = ref(false)
const batchLoading = ref(false)
const executeLoading = ref(false)

// 批量导入表单
const batchForm = reactive({
  keywords: '',
  autoFocus: false
})

// 执行任务表单
const executeForm = reactive({
  type: 'daily' as 'daily' | 'historical'
})

// 获取标签列表
const fetchTags = async () => {
  try {
    const response = await tagsApi.getList()
    if (response.err_code === 0) {
      tags.value = response.payload.data
    } else {
      ElMessage.error(response.err_msg || '获取标签列表失败')
    }
  } catch (error) {
    console.error('获取标签列表失败:', error)
    ElMessage.error('获取标签列表失败')
  }
}

// 标签变更处理
const handleTagChange = (tagId: number) => {
  selectedTagId.value = tagId
}

// 添加成功处理
const handleAddSuccess = () => {
  showAddDialog.value = false
  fetchTags()
  ElMessage.success('添加成功')
}

// 关键词添加成功处理
const handleKeywordSuccess = () => {
  showKeywordDialog.value = false
  ElMessage.success('关键词添加成功')
}

// 批量导入处理
const handleBatchImport = async () => {
  if (!selectedTagId.value) {
    ElMessage.warning('请先选择标签')
    return
  }

  if (!batchForm.keywords.trim()) {
    ElMessage.warning('请输入关键词')
    return
  }

  batchLoading.value = true
  try {
    const keywords = batchForm.keywords
      .split('\n')
      .map(k => k.trim())
      .filter(k => k.length > 0)

    if (keywords.length === 0) {
      ElMessage.warning('请输入有效的关键词')
      return
    }

    const response = await tagsApi.batchCreateKeywords({
      tag_id: selectedTagId.value,
      keywords: keywords,
      auto_focus: batchForm.autoFocus
    })

    if (response.err_code === 0) {
      const result = response.payload
      ElMessage.success(`批量导入完成：成功 ${result.success_count} 个，失败 ${result.failed_keywords.length} 个`)
      showBatchDialog.value = false
      batchForm.keywords = ''
      batchForm.autoFocus = false
    } else {
      ElMessage.error(response.err_msg || '批量导入失败')
    }
  } catch (error) {
    console.error('批量导入失败:', error)
    ElMessage.error('批量导入失败')
  } finally {
    batchLoading.value = false
  }
}

// 执行任务处理
const handleExecuteTask = async () => {
  executeLoading.value = true
  try {
    const response = await tagsApi.executeAutoTagging({
      type: executeForm.type
    })

    if (response.err_code === 0) {
      ElMessage.success(`任务已提交，任务ID: ${response.payload.task_id}`)
      showExecuteDialog.value = false
    } else {
      ElMessage.error(response.err_msg || '任务提交失败')
    }
  } catch (error) {
    console.error('任务执行失败:', error)
    ElMessage.error('任务执行失败')
  } finally {
    executeLoading.value = false
  }
}

// 任务执行处理
const handleTaskExecuted = () => {
  ElMessage.success('任务执行成功')
}

// 页面加载时获取数据
onMounted(() => {
  fetchTags()
})
</script>

<style scoped>
.tag-keyword-mapping {
  height: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.tag-selector {
  margin-bottom: 24px;
}

.keywords-section {
  margin-top: 24px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.section-actions {
  display: flex;
  gap: 8px;
}

.control-panel {
  margin-top: 32px;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
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