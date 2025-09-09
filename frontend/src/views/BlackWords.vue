<template>
  <div class="black-words">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>黑词管理</span>
          <div class="header-actions">
            <el-button type="primary" @click="showAddDialog = true">添加黑词</el-button>
            <el-button @click="downloadData">导出数据</el-button>
          </div>
        </div>
      </template>
      
      <!-- 黑词表格区域 -->
      <div class="table-area">
        <div class="table-container">
          <el-table 
            :data="keywordList" 
            v-loading="loading"
            :max-height="tableMaxHeight"
            stripe
            highlight-current-row
            empty-text="暂无黑词数据"
            row-key="id"
            style="width: 100%;"
          >
            <el-table-column type="index" width="60" label="#" />
            
            <el-table-column prop="keyword" label="关键词" min-width="200" show-overflow-tooltip>
              <template #default="{ row }">
                <span class="keyword-text">{{ row.keyword }}</span>
              </template>
            </el-table-column>
            
            <el-table-column prop="status" label="状态" width="100" align="center">
              <template #default="{ row }">
                <el-tag :type="getStatusType(row.status)" size="small">
                  {{ getStatusText(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            
            <el-table-column prop="is_delete" label="删除状态" width="120" align="center">
              <template #default="{ row }">
                <el-tag :type="row.is_delete ? 'danger' : 'success'" size="small">
                  {{ row.is_delete ? '已删除' : '正常' }}
                </el-tag>
              </template>
            </el-table-column>
            
            <el-table-column prop="created_at" label="创建时间" width="150" show-overflow-tooltip>
              <template #default="{ row }">
                <span class="time-text">{{ formatDateTime(row.created_at) }}</span>
              </template>
            </el-table-column>
            
            <el-table-column prop="updated_at" label="更新时间" width="150" show-overflow-tooltip>
              <template #default="{ row }">
                <span class="time-text">{{ formatDateTime(row.updated_at) }}</span>
              </template>
            </el-table-column>
            
            <el-table-column label="操作" width="200" align="center" fixed="right">
              <template #default="{ row }">
                <el-button 
                  type="primary" 
                  size="small" 
                  @click="editKeyword(row)"
                >
                  编辑
                </el-button>
                <el-button 
                  :type="row.status === 0 ? 'warning' : 'success'" 
                  size="small" 
                  @click="toggleStatus(row)"
                  :loading="statusLoading"
                >
                  {{ row.status === 0 ? '禁用' : '启用' }}
                </el-button>
                <el-button 
                  type="danger" 
                  size="small" 
                  @click="deleteKeyword(row)"
                  :loading="deleteLoading"
                >
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
        
        <!-- 分页组件 -->
        <div class="pagination-container">
          <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :page-sizes="[10, 20, 50, 100]"
            :total="total"
            layout="total, sizes, prev, pager, next, jumper"
            background
            @size-change="handleSizeChange"
            @current-change="handlePageChange"
          />
        </div>
      </div>
    </el-card>

    <!-- 添加黑词对话框 -->
    <el-dialog v-model="showAddDialog" title="添加黑词" width="450px">
      <el-form :model="addForm" ref="addFormRef" :rules="formRules" label-width="80px">
        <el-form-item label="关键词" prop="keyword">
          <el-input 
            v-model="addForm.keyword" 
            placeholder="请输入关键词" 
            maxlength="126"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-radio-group v-model="addForm.status">
            <el-radio :label="0">启用</el-radio>
            <el-radio :label="1">禁用</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="addKeyword" :loading="addLoading">确定</el-button>
      </template>
    </el-dialog>

    <!-- 编辑黑词对话框 -->
    <el-dialog v-model="showEditDialog" title="编辑黑词" width="450px">
      <el-form :model="editForm" ref="editFormRef" :rules="formRules" label-width="80px">
        <el-form-item label="关键词" prop="keyword">
          <el-input 
            v-model="editForm.keyword" 
            placeholder="请输入关键词" 
            maxlength="126"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-radio-group v-model="editForm.status">
            <el-radio :label="0">启用</el-radio>
            <el-radio :label="1">禁用</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" @click="updateKeyword" :loading="editLoading">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, nextTick, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { blackWordsApi, type BlackKeyword } from '@/api/black-words'
import { formatUTCToLocal } from '@/utils/date'

// 页面元信息
defineOptions({
  name: 'BlackWords'
})

// 响应式数据
const loading = ref(false)
const addLoading = ref(false)
const editLoading = ref(false)
const statusLoading = ref(false)
const deleteLoading = ref(false)
const showAddDialog = ref(false)
const showEditDialog = ref(false)
const keywordList = ref<BlackKeyword[]>([])

// 表格高度计算
const tableMaxHeight = ref(400)

// 分页数据
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

// 表单引用
const addFormRef = ref<FormInstance>()
const editFormRef = ref<FormInstance>()

// 添加表单
const addForm = reactive({
  keyword: '',
  status: 0
})

// 编辑表单
const editForm = reactive({
  id: 0,
  keyword: '',
  status: 0
})

// 表单验证规则
const formRules: FormRules = {
  keyword: [
    { required: true, message: '请输入关键词', trigger: 'blur' },
    { min: 1, max: 126, message: '关键词长度应在1-126个字符之间', trigger: 'blur' }
  ],
  status: [
    { required: true, message: '请选择状态', trigger: 'change' }
  ]
}

// 获取数据
const fetchData = async () => {
  loading.value = true
  
  try {
    const response = await blackWordsApi.getList({
      page: currentPage.value,
      page_size: pageSize.value
    })
    
    if (response.data.err_code === 0) {
      keywordList.value = response.data.payload.data || []
      total.value = response.data.payload.total || 0
    } else {
      ElMessage.error(response.data.err_msg || '获取数据失败')
      keywordList.value = []
      total.value = 0
    }
  } catch (error) {
    console.error('获取数据失败:', error)
    ElMessage.error('获取数据失败')
    keywordList.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

// 分页变化处理
const handlePageChange = (page: number) => {
  currentPage.value = page
  fetchData()
}

// 每页大小变化处理
const handleSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1
  fetchData()
}

// 添加黑词
const addKeyword = async () => {
  if (!addFormRef.value) return
  
  try {
    await addFormRef.value.validate()
    
    addLoading.value = true
    
    const response = await blackWordsApi.create({
      keyword: addForm.keyword,
      status: addForm.status
    })
    
    if (response.data.err_code === 0) {
      ElMessage.success('添加成功')
      showAddDialog.value = false
      addForm.keyword = ''
      addForm.status = 0
      fetchData()
    } else {
      ElMessage.error(response.data.err_msg || '添加失败')
    }
  } catch (error) {
    console.error('添加黑词失败:', error)
    ElMessage.error('添加失败')
  } finally {
    addLoading.value = false
  }
}

// 编辑黑词
const editKeyword = (keyword: BlackKeyword) => {
  editForm.id = keyword.id
  editForm.keyword = keyword.keyword
  editForm.status = keyword.status
  showEditDialog.value = true
}

// 更新黑词
const updateKeyword = async () => {
  if (!editFormRef.value) return
  
  try {
    await editFormRef.value.validate()
    
    editLoading.value = true
    
    const response = await blackWordsApi.update(editForm.id, {
      keyword: editForm.keyword,
      status: editForm.status
    })
    
    if (response.data.err_code === 0) {
      ElMessage.success('更新成功')
      showEditDialog.value = false
      fetchData()
    } else {
      ElMessage.error(response.data.err_msg || '更新失败')
    }
  } catch (error) {
    console.error('更新黑词失败:', error)
    ElMessage.error('更新失败')
  } finally {
    editLoading.value = false
  }
}

// 切换状态
const toggleStatus = async (keyword: BlackKeyword) => {
  try {
    const newStatus = keyword.status === 0 ? 1 : 0
    const action = newStatus === 0 ? '启用' : '禁用'
    
    await ElMessageBox.confirm(`确认${action}关键词"${keyword.keyword}"?`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    statusLoading.value = true
    
    const response = await blackWordsApi.update(keyword.id, {
      keyword: keyword.keyword,
      status: newStatus
    })
    
    if (response.data.err_code === 0) {
      ElMessage.success(`${action}成功`)
      fetchData()
    } else {
      ElMessage.error(response.data.err_msg || `${action}失败`)
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('切换状态失败:', error)
      ElMessage.error('操作失败')
    }
  } finally {
    statusLoading.value = false
  }
}

// 删除黑词
const deleteKeyword = async (keyword: BlackKeyword) => {
  try {
    await ElMessageBox.confirm(`确认删除关键词"${keyword.keyword}"?`, '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    deleteLoading.value = true
    
    const response = await blackWordsApi.delete(keyword.id)
    
    if (response.data.err_code === 0) {
      ElMessage.success('删除成功')
      fetchData()
    } else {
      ElMessage.error(response.data.err_msg || '删除失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除黑词失败:', error)
      ElMessage.error('删除失败')
    }
  } finally {
    deleteLoading.value = false
  }
}

// 下载数据
const downloadData = async () => {
  try {
    ElMessage.success('导出功能开发中')
  } catch (error) {
    ElMessage.error('导出失败')
  }
}

// 获取状态类型
const getStatusType = (status: number) => {
  return status === 0 ? 'success' : 'danger'
}

// 获取状态文本
const getStatusText = (status: number) => {
  return status === 0 ? '启用' : '禁用'
}

// 格式化日期时间
const formatDateTime = (dateTime: string): string => {
  if (!dateTime) return '-'
  try {
    return formatUTCToLocal(dateTime, 'YYYY-MM-DD HH:mm:ss')
  } catch (error) {
    return '-'
  }
}

// 计算表格最大高度
const calculateTableMaxHeight = () => {
  nextTick(() => {
    const windowHeight = window.innerHeight
    const cardHeaderHeight = 70
    const paginationHeight = 80
    const padding = 40
    
    const availableHeight = windowHeight - cardHeaderHeight - paginationHeight - padding
    tableMaxHeight.value = Math.max(400, availableHeight)
  })
}

// 窗口大小变化监听
const handleResize = () => {
  calculateTableMaxHeight()
}

// 页面加载时获取数据
onMounted(() => {
  document.body.style.overflow = 'hidden'
  fetchData()
  calculateTableMaxHeight()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  document.body.style.overflow = 'auto'
  window.removeEventListener('resize', handleResize)
})
</script>

<style lang="scss" scoped>
.black-words {
  height: 100vh;
  padding: 0;
  margin: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.black-words > .el-card {
  width: 100%;
  flex: 1;
  margin: 0;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.black-words > .el-card > .el-card__body {
  padding: 20px;
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-height: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 10px;
}

/* 表格区域布局 */
.table-area {
  margin-top: 0;
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
}

.table-container {
  flex: 1;
  border-radius: 8px 8px 0 0;
  border: 1px solid #e4e7ed;
  border-bottom: none;
  margin-bottom: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

/* 表格样式 */
:deep(.el-table) {
  height: 100%;
  display: flex;
  flex-direction: column;
  
  .el-table__header-wrapper {
    flex-shrink: 0;
    overflow: visible !important;
  }
  
  .el-table__body-wrapper {
    flex: 1;
    overflow-y: auto !important;
    overflow-x: hidden;
  }
  
  .el-table__fixed-header-wrapper {
    overflow: visible !important;
  }
}

/* 表格单元格样式 */
.keyword-text {
  font-weight: 500;
  color: #303133;
}

.time-text {
  font-size: 12px;
  color: #909399;
}

/* 分页组件样式 */
.pagination-container {
  display: flex !important;
  justify-content: center;
  align-items: center;
  padding: 16px 20px;
  border-top: 1px solid #e4e7ed;
  background-color: #fafafa;
  border-radius: 0 0 8px 8px;
  border-left: 1px solid #e4e7ed;
  border-right: 1px solid #e4e7ed;
  border-bottom: 1px solid #e4e7ed;
  min-height: 60px;
  width: 100%;
  flex-shrink: 0;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .header-actions {
    flex-direction: column;
    gap: 8px;
  }
}
</style>