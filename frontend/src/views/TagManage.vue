<template>
  <div class="tag-manage">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>标签管理</span>
          <el-button type="primary" @click="showAddDialog = true">添加标签</el-button>
        </div>
      </template>
      
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
          <el-table-column label="操作" width="200" fixed="right">
            <template #default="{ row }">
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
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance } from 'element-plus'
import { tagsApi, type Tag } from '@/api/tags'

// 响应式数据
const loading = ref(false)
const addLoading = ref(false)
const editLoading = ref(false)
const showAddDialog = ref(false)
const showEditDialog = ref(false)
const tableData = ref<Tag[]>([])

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
</style>