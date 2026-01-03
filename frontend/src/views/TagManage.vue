<template>
  <div class="tag-manage">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>标签管理</span>
          <el-button type="primary" @click="showAddDialog = true">添加标签</el-button>
        </div>
      </template>

      <!-- 标签管理内容 -->
      <div v-loading="loading" class="content">
            <el-table
              :data="tableData"
              style="width: 100%"
              stripe
              @row-click="handleRowClick"
              :row-class-name="() => 'clickable-row'"
            >
              <!-- 标签名称（带颜色） -->
              <el-table-column prop="name" label="标签" width="200">
                <template #default="{ row }">
                  <el-tag
                    :color="row.color"
                    effect="dark"
                    size="large"
                    style="color: white; border: none; font-size: 14px; padding: 8px 16px;"
                  >
                    {{ row.name }}
                  </el-tag>
                </template>
              </el-table-column>

              <!-- 绑定关键词 -->
              <el-table-column label="自动标签绑定关键词">
                <template #default="{ row }">
                  <div class="keywords-preview">
                    <template v-if="row.keywordsTotal > 0">
                      <span
                        v-for="(kw, idx) in row.keywords"
                        :key="idx"
                        class="keyword-chip"
                      >
                        {{ kw.keyword }}
                      </span>
                      <span v-if="row.keywordsTotal > row.keywords.length" class="more-count">
                        (+{{ row.keywordsTotal - row.keywords.length }})
                      </span>
                    </template>
                    <el-tag v-else type="info" size="small" effect="plain">
                      暂无关键词
                    </el-tag>
                  </div>
                </template>
              </el-table-column>

              <!-- 操作 -->
              <el-table-column label="操作" width="200" align="center">
                <template #default="{ row }">
                  <div class="action-buttons">
                    <el-button
                      type="primary"
                      size="small"
                      :icon="Plus"
                      @click.stop="openBatchImport(row)"
                    >
                      添加关键词
                    </el-button>
                    <el-button
                      type="warning"
                      size="small"
                      :icon="Edit"
                      @click.stop="editTag(row)"
                    >
                      修改标签
                    </el-button>
                  </div>
                </template>
              </el-table-column>
            </el-table>

            <!-- 展开的关键词详情面板 -->
            <el-collapse-transition>
              <div v-if="expandedTagId" class="keyword-detail-panel">
                <div class="panel-header">
                  <h3>
                    <span>关键词管理 - </span>
                    <el-tag
                      :color="expandedTag?.color"
                      effect="dark"
                      size="large"
                      style="color: white; border: none;"
                    >
                      {{ expandedTag?.name }}
                    </el-tag>
                  </h3>
                  <div class="panel-actions">
                    <el-button
                      size="small"
                      :icon="Close"
                      @click="expandedTagId = null"
                    >
                      收起
                    </el-button>
                  </div>
                </div>
                <KeywordList
                  :tag-id="expandedTagId"
                  :key="expandedTagId"
                  @refresh="fetchData"
                />
              </div>
            </el-collapse-transition>
      </div>
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
        <el-form-item label="NSFW标记" prop="is_nsfw">
          <el-switch
            v-model="addForm.is_nsfw"
            active-text="是"
            inactive-text="否"
          />
          <div class="form-tip">标记为NSFW的标签将对群组图片应用模糊效果</div>
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
        <el-form-item label="NSFW标记" prop="is_nsfw">
          <el-switch
            v-model="editForm.is_nsfw"
            active-text="是"
            inactive-text="否"
          />
          <div class="form-tip">标记为NSFW的标签将对群组图片应用模糊效果</div>
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

  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Close, Edit } from '@element-plus/icons-vue'
import type { FormInstance } from 'element-plus'
import { tagsApi, type Tag } from '@/api/tags'
import KeywordForm from '@/views/components/KeywordForm.vue'
import KeywordList from '@/views/components/KeywordList.vue'

// 响应式数据
const loading = ref(false)
const addLoading = ref(false)
const editLoading = ref(false)
const batchLoading = ref(false)
const showAddDialog = ref(false)
const showEditDialog = ref(false)
const showKeywordDialog = ref(false)
const showBatchDialog = ref(false)
const tableData = ref<Tag[]>([])
const selectedTagId = ref<number>()
const expandedTagId = ref<number | null>(null)
const currentBatchTagId = ref<number>()

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
  color: '#409EFF',
  is_nsfw: false
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
  color: '#409EFF',
  is_nsfw: false
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

// 计算属性：当前展开的标签
const expandedTag = computed(() => {
  return tableData.value.find(tag => tag.id === expandedTagId.value)
})

// 获取标签列表（带关键词）
const fetchData = async () => {
  loading.value = true
  try {
    const response = await tagsApi.getList()
    if (response.err_code === 0) {
      // 为每个标签加载关键词（只获取前5个用于预览，但要获取总数）
      const tagsWithKeywords = await Promise.all(
        response.payload.data.map(async (tag) => {
          try {
            const keywordsResp = await tagsApi.getKeywordMappings(tag.id, {
              page: 1,
              page_size: 5,  // 只获取前5个用于预览
              is_active: true
            })
            return {
              ...tag,
              keywords: keywordsResp.err_code === 0 ? keywordsResp.payload.data : [],
              keywordsTotal: keywordsResp.err_code === 0 ? keywordsResp.payload.total : 0  // 保存总数
            }
          } catch (error) {
            console.error(`获取标签 ${tag.id} 关键词失败:`, error)
            return { ...tag, keywords: [], keywordsTotal: 0 }
          }
        })
      )
      tableData.value = tagsWithKeywords
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

// 点击表格行
const handleRowClick = (row: Tag) => {
  // 切换展开/收起
  if (expandedTagId.value === row.id) {
    expandedTagId.value = null
  } else {
    expandedTagId.value = row.id
    selectedTagId.value = row.id
  }
}

// 打开批量导入对话框
const openBatchImport = (row: Tag) => {
  currentBatchTagId.value = row.id
  selectedTagId.value = row.id
  showBatchDialog.value = true
}

// 添加标签
const addTag = async () => {
  if (!addFormRef.value) return
  
  try {
    await addFormRef.value.validate()
    addLoading.value = true

    const response = await tagsApi.add({
      name: addForm.name,
      color: addForm.color,
      is_nsfw: addForm.is_nsfw
    })
    if (response.err_code === 0) {
      ElMessage.success('添加成功')
      showAddDialog.value = false
      addForm.name = ''
      addForm.color = '#409EFF'
      addForm.is_nsfw = false
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
  editForm.is_nsfw = row.is_nsfw || false
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
      color: editForm.color,
      is_nsfw: editForm.is_nsfw
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
    // 错误消息已经在axios拦截器中显示,这里不需要再显示
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

// 关键词添加成功处理
const handleKeywordSuccess = () => {
  showKeywordDialog.value = false
  ElMessage.success('关键词添加成功')
}

// 批量导入处理
const handleBatchImport = async () => {
  const tagId = currentBatchTagId.value || selectedTagId.value

  if (!tagId) {
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
      tag_id: tagId,
      keywords: keywords,
      auto_focus: batchForm.autoFocus
    })

    if (response.err_code === 0) {
      const result = response.payload
      ElMessage.success(`批量导入完成：成功 ${result.success_count} 个，失败 ${result.failed_keywords.length} 个`)
      showBatchDialog.value = false
      batchForm.keywords = ''
      batchForm.autoFocus = false

      // 刷新标签列表数据
      await fetchData()

      // 如果当前有展开的关键词面板，刷新该面板
      // 通过改变 key 来强制 KeywordList 组件重新加载
      if (expandedTagId.value === tagId) {
        const currentId = expandedTagId.value
        expandedTagId.value = null
        await nextTick()
        expandedTagId.value = currentId
      }
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

/* 可点击的表格行 */
:deep(.clickable-row) {
  cursor: pointer;
  transition: background-color 0.2s;
}

:deep(.clickable-row:hover) {
  background-color: #f5f7fa !important;
}

/* 操作按钮 */
.action-buttons {
  display: flex;
  gap: 8px;
  justify-content: center;
  flex-wrap: nowrap;
}

/* 关键词预览 */
.keywords-preview {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
}

.keyword-chip {
  display: inline-block;
  padding: 2px 8px;
  background: #ecf5ff;
  color: #409eff;
  border-radius: 4px;
  font-size: 12px;
}

.more-count {
  color: #909399;
  font-size: 12px;
}

/* 关键词详情面板 */
.keyword-detail-panel {
  margin-top: 20px;
  padding: 20px;
  background: #f5f7fa;
  border-radius: 8px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #dcdfe6;
}

.panel-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
}

.panel-actions {
  display: flex;
  gap: 8px;
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

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}
</style>