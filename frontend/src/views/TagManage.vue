<template>
  <div class="tag-manage">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>标签管理</span>
          <div class="header-actions">
            <el-button
              v-if="activeTab === 'auto-tagging'"
              type="success"
              :icon="CaretRight"
              @click="showExecuteDialog = true"
            >
              执行自动标签任务
            </el-button>
            <el-button type="primary" @click="showAddDialog = true">添加标签</el-button>
          </div>
        </div>
      </template>

      <!-- 标签页 -->
      <el-tabs v-model="activeTab" class="tag-tabs">
        <!-- 基础标签管理 -->
        <el-tab-pane label="标签管理" name="basic">
          <div v-loading="loading" class="content">
            <el-table :data="tableData" style="width: 100%" stripe>
          <el-table-column prop="id" label="ID" width="80" />
          <el-table-column prop="name" label="标签名称">
            <template #default="{ row }">
              <el-tag :color="row.color" effect="dark" style="color: white; border: none;">
                {{ row.name }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="color" label="颜色" width="80">
            <template #default="{ row }">
              <div 
                :style="{ 
                  width: '20px', 
                  height: '20px', 
                  backgroundColor: row.color, 
                  borderRadius: '4px',
                  border: '1px solid #dcdfe6'
                }"
              ></div>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="row.status === '有效' ? 'success' : 'danger'">
                {{ row.status }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" width="180" />
          <el-table-column prop="updated_at" label="更新时间" width="180" />
          <el-table-column label="操作" width="280" fixed="right">
            <template #default="{ row }">
              <el-button
                type="info"
                size="small"
                @click="viewKeywords(row)"
              >
                关键词
              </el-button>
              <el-button
                type="primary"
                size="small"
                @click="editTag(row)"
              >
                编辑
              </el-button>
              <el-button
                type="danger"
                size="small"
                @click="deleteTag(row)"
              >
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
          </div>
        </el-tab-pane>

        <!-- 自动标签 -->
        <el-tab-pane label="自动标签" name="auto-tagging">
          <div class="auto-tagging-section">
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
                  v-for="tag in tableData"
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
                @refresh="fetchData"
              />
            </div>

            <!-- 控制面板 -->
            <div class="control-panel">
              <AutoTaggingControl @task-executed="handleTaskExecuted" />
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- 添加标签对话框 -->
    <el-dialog v-model="showAddDialog" title="添加标签" width="400px">
      <el-form :model="addForm" :rules="addRules" ref="addFormRef">
        <el-form-item label="标签名称" prop="name">
          <el-input 
            v-model="addForm.name" 
            placeholder="请输入标签名称"
            maxlength="32"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="标签颜色" prop="color">
          <div class="color-picker">
            <div 
              v-for="colorOption in colorOptions" 
              :key="colorOption"
              class="color-option"
              :class="{ active: addForm.color === colorOption }"
              :style="{ backgroundColor: colorOption }"
              @click="addForm.color = colorOption"
            ></div>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="addTag" :loading="addLoading">确定</el-button>
      </template>
    </el-dialog>

    <!-- 编辑标签对话框 -->
    <el-dialog v-model="showEditDialog" title="编辑标签" width="400px">
      <el-form :model="editForm" :rules="editRules" ref="editFormRef">
        <el-form-item label="标签名称" prop="name">
          <el-input 
            v-model="editForm.name" 
            placeholder="请输入标签名称"
            maxlength="32"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="标签颜色" prop="color">
          <div class="color-picker">
            <div 
              v-for="colorOption in colorOptions" 
              :key="colorOption"
              class="color-option"
              :class="{ active: editForm.color === colorOption }"
              :style="{ backgroundColor: colorOption }"
              @click="editForm.color = colorOption"
            ></div>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" @click="updateTag" :loading="editLoading">保存</el-button>
      </template>
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
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, CaretRight, DocumentAdd } from '@element-plus/icons-vue'
import type { FormInstance } from 'element-plus'
import { tagsApi, type Tag } from '@/api/tags'
import KeywordForm from '@/views/components/KeywordForm.vue'
import KeywordList from '@/views/components/KeywordList.vue'
import AutoTaggingControl from '@/views/components/AutoTaggingControl.vue'

// 响应式数据
const loading = ref(false)
const addLoading = ref(false)
const editLoading = ref(false)
const batchLoading = ref(false)
const executeLoading = ref(false)
const showAddDialog = ref(false)
const showEditDialog = ref(false)
const showKeywordDialog = ref(false)
const showBatchDialog = ref(false)
const showExecuteDialog = ref(false)
const tableData = ref<Tag[]>([])
const activeTab = ref('basic')
const selectedTagId = ref<number>()

// 表单引用
const addFormRef = ref<FormInstance>()
const editFormRef = ref<FormInstance>()

// 颜色选项
const colorOptions = [
  '#409EFF',
  '#67C23A', 
  '#F56C6C',
  '#E6A23C',
  '#9B59B6',
  '#1ABC9C',
  '#909399',
  '#FFB6C1'
]

// 添加表单
const addForm = reactive({
  name: '',
  color: '#409EFF'
})

const addRules = {
  name: [
    { required: true, message: '请输入标签名称', trigger: 'blur' },
    { min: 1, max: 32, message: '标签名称长度在1到32个字符之间', trigger: 'blur' }
  ]
}

// 编辑表单
const editForm = reactive({
  id: 0,
  name: '',
  color: '#409EFF'
})

const editRules = {
  name: [
    { required: true, message: '请输入标签名称', trigger: 'blur' },
    { min: 1, max: 32, message: '标签名称长度在1到32个字符之间', trigger: 'blur' }
  ]
}

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
const fetchData = async () => {
  loading.value = true
  try {
    const response = await tagsApi.getList()
    if (response.err_code === 0) {
      tableData.value = response.payload.data
    } else {
      ElMessage.error(response.err_msg || '获取标签列表失败')
    }
  } catch (error) {
    console.error('获取标签列表失败:', error)
    ElMessage.error('获取标签列表失败')
  } finally {
    loading.value = false
  }
}

// 添加标签
const addTag = async () => {
  if (!addFormRef.value) return
  
  try {
    await addFormRef.value.validate()
    addLoading.value = true
    
    const response = await tagsApi.add({ name: addForm.name, color: addForm.color })
    if (response.err_code === 0) {
      ElMessage.success('添加成功')
      showAddDialog.value = false
      addForm.name = ''
      addForm.color = '#409EFF'
      fetchData()
    } else {
      ElMessage.error(response.err_msg || '添加失败')
    }
  } catch (error) {
    console.error('添加标签失败:', error)
    ElMessage.error('添加失败')
  } finally {
    addLoading.value = false
  }
}

// 编辑标签
const editTag = (row: Tag) => {
  editForm.id = row.id
  editForm.name = row.name
  editForm.color = row.color || '#409EFF'
  showEditDialog.value = true
}

// 更新标签
const updateTag = async () => {
  if (!editFormRef.value) return
  
  try {
    await editFormRef.value.validate()
    editLoading.value = true
    
    const response = await tagsApi.edit({
      id: editForm.id,
      name: editForm.name,
      color: editForm.color
    })
    
    if (response.err_code === 0) {
      ElMessage.success('更新成功')
      showEditDialog.value = false
      fetchData()
    } else {
      ElMessage.error(response.err_msg || '更新失败')
    }
  } catch (error) {
    console.error('更新标签失败:', error)
    ElMessage.error('更新失败')
  } finally {
    editLoading.value = false
  }
}

// 删除标签
const deleteTag = async (row: Tag) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除标签"${row.name}"吗？`,
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const response = await tagsApi.delete(row.id)
    if (response.err_code === 0) {
      ElMessage.success('删除成功')
      fetchData()
    } else {
      ElMessage.error(response.err_msg || '删除失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除标签失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

// 查看关键词（切换到自动标签页）
const viewKeywords = (row: Tag) => {
  activeTab.value = 'auto-tagging'
  selectedTagId.value = row.id
}

// 标签变更处理
const handleTagChange = (tagId: number) => {
  selectedTagId.value = tagId
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
  fetchData()
})
</script>

<style scoped>
.tag-manage {
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

.content {
  min-height: 400px;
}

.color-picker {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.color-option {
  width: 32px;
  height: 32px;
  border-radius: 6px;
  cursor: pointer;
  border: 2px solid transparent;
  transition: all 0.2s ease;
}

.color-option:hover {
  transform: scale(1.1);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.color-option.active {
  border-color: #ffffff;
  box-shadow: 0 0 0 2px #409eff;
  transform: scale(1.1);
}

.tag-tabs {
  margin-top: 16px;
}

.auto-tagging-section {
  display: flex;
  flex-direction: column;
  gap: 24px;
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