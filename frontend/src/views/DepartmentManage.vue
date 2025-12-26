<template>
  <div class="department-manage">
    <el-card class="table-card">
      <template #header>
        <div class="card-header">
          <span>部门管理</span>
          <el-button type="primary" @click="showAddDialog = true">
            <el-icon><Plus /></el-icon>
            添加部门
          </el-button>
        </div>
      </template>

      <!-- 部门列表表格 -->
      <el-table :data="departments" style="width: 100%" v-loading="loading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="部门名称" width="200" />
        <el-table-column prop="description" label="描述" min-width="250" show-overflow-tooltip />
        <el-table-column prop="user_count" label="用户数" width="100" align="center" />
        <el-table-column prop="tg_account_count" label="关联TG账户" width="120" align="center" />
        <el-table-column label="状态" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.is_active === 1 ? 'success' : 'danger'" size="small">
              {{ scope.row.is_active === 1 ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="160" />
        <el-table-column label="操作" width="300" fixed="right">
          <template #default="scope">
            <el-button
              type="primary"
              size="small"
              @click="handleEdit(scope.row)"
              :disabled="scope.row.id === 0"
            >
              编辑
            </el-button>
            <el-button
              type="success"
              size="small"
              @click="handleManageTgAccounts(scope.row)"
              :disabled="scope.row.id === 0"
            >
              配置TG账户
            </el-button>
            <el-button
              size="small"
              type="danger"
              @click="handleDelete(scope.row)"
              :disabled="scope.row.id === 0 || scope.row.user_count > 0"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 添加/编辑部门对话框 -->
    <el-dialog
      v-model="showAddDialog"
      :title="isEditing ? '编辑部门' : '添加部门'"
      width="500px"
    >
      <el-form :model="departmentForm" :rules="departmentRules" ref="departmentFormRef" label-width="100px">
        <el-form-item label="部门名称" prop="name">
          <el-input v-model="departmentForm.name" placeholder="请输入部门名称" />
        </el-form-item>
        <el-form-item label="部门描述" prop="description">
          <el-input
            v-model="departmentForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入部门描述"
          />
        </el-form-item>
        <el-form-item label="状态" v-if="isEditing">
          <el-switch
            v-model="departmentForm.is_active"
            :active-value="1"
            :inactive-value="0"
            active-text="启用"
            inactive-text="禁用"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>

    <!-- TG账户关联配置对话框 -->
    <el-dialog
      v-model="showTgAccountDialog"
      title="配置TG账户关联"
      width="700px"
    >
      <div v-if="currentDepartment">
        <p style="margin-bottom: 16px; color: #606266;">
          为 <strong>{{ currentDepartment.name }}</strong> 配置可访问的TG账户
        </p>

        <!-- 穿梭框 -->
        <el-transfer
          v-model="selectedTgAccountIds"
          :data="transferData"
          :titles="['可用TG账户', '已关联TG账户']"
          :props="{
            key: 'value',
            label: 'label'
          }"
          filterable
          filter-placeholder="搜索账户"
          style="text-align: left"
        />
      </div>
      <template #footer>
        <el-button @click="showTgAccountDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSubmitTgAccounts" :loading="submitting">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { useDepartmentStore } from '@/store/department'
import type { Department } from '@/api/department'
import { getDepartmentTgAccounts, updateDepartmentTgAccounts } from '@/api/department'

// Store
const departmentStore = useDepartmentStore()

// 响应式数据
const loading = ref(false)
const showAddDialog = ref(false)
const showTgAccountDialog = ref(false)
const isEditing = ref(false)
const submitting = ref(false)
const currentDepartment = ref<Department | null>(null)
const selectedTgAccountIds = ref<string[]>([])

// 表单数据
const departmentForm = ref({
  id: 0,
  name: '',
  description: '',
  is_active: 1
})

// 表单验证规则
const departmentRules = {
  name: [
    { required: true, message: '请输入部门名称', trigger: 'blur' },
    { min: 2, max: 50, message: '部门名称长度在 2 到 50 个字符', trigger: 'blur' }
  ]
}

const departmentFormRef = ref()

// 计算属性
const departments = computed(() => departmentStore.departments)

// 穿梭框数据
const transferData = computed(() => {
  return departmentStore.availableTgAccounts.map(account => ({
    value: account.user_id,
    label: account.display_name,
    disabled: false
  }))
})

// 加载部门列表
const loadDepartments = async () => {
  loading.value = true
  try {
    await departmentStore.fetchDepartments()
  } catch (error: any) {
    ElMessage.error('加载部门列表失败: ' + (error.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

// 编辑部门
const handleEdit = (department: Department) => {
  isEditing.value = true
  departmentForm.value = {
    id: department.id,
    name: department.name,
    description: department.description || '',
    is_active: department.is_active
  }
  showAddDialog.value = true
}

// 提交表单
const handleSubmit = async () => {
  if (!departmentFormRef.value) return

  await departmentFormRef.value.validate(async (valid: boolean) => {
    if (!valid) return

    submitting.value = true
    try {
      if (isEditing.value) {
        // 更新部门
        const res = await departmentStore.modifyDepartment(departmentForm.value.id, {
          name: departmentForm.value.name,
          description: departmentForm.value.description,
          is_active: departmentForm.value.is_active
        })
        if (res.err_code === 0) {
          ElMessage.success('更新成功')
          showAddDialog.value = false
          resetForm()
        } else {
          ElMessage.error(res.err_msg || '更新失败')
        }
      } else {
        // 创建部门
        const res = await departmentStore.addDepartment({
          name: departmentForm.value.name,
          description: departmentForm.value.description
        })
        if (res.err_code === 0) {
          ElMessage.success('创建成功')
          showAddDialog.value = false
          resetForm()
        } else {
          ElMessage.error(res.err_msg || '创建失败')
        }
      }
    } catch (error: any) {
      ElMessage.error('操作失败: ' + (error.message || '未知错误'))
    } finally {
      submitting.value = false
    }
  })
}

// 删除部门
const handleDelete = async (department: Department) => {
  if (department.id === 0) {
    ElMessage.warning('不允许删除全局部门')
    return
  }

  if (department.user_count > 0) {
    ElMessage.warning(`该部门还有 ${department.user_count} 个用户，无法删除`)
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定要删除部门 "${department.name}" 吗？此操作不可恢复。`,
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    const res = await departmentStore.removeDepartment(department.id)
    if (res.err_code === 0) {
      ElMessage.success('删除成功')
    } else {
      ElMessage.error(res.err_msg || '删除失败')
    }
  } catch {
    // 用户取消删除
  }
}

// 管理TG账户关联
const handleManageTgAccounts = async (department: Department) => {
  currentDepartment.value = department

  // 加载可用的TG账户列表
  await departmentStore.fetchAvailableTgAccounts()

  // 加载该部门已关联的TG账户
  try {
    const res = await getDepartmentTgAccounts(department.id)
    if (res.err_code === 0) {
      selectedTgAccountIds.value = res.payload.data.map(item => item.tg_user_id)
    }
  } catch (error: any) {
    ElMessage.error('加载关联账户失败: ' + (error.message || '未知错误'))
  }

  showTgAccountDialog.value = true
}

// 提交TG账户关联
const handleSubmitTgAccounts = async () => {
  if (!currentDepartment.value) return

  submitting.value = true
  try {
    const res = await updateDepartmentTgAccounts(
      currentDepartment.value.id,
      selectedTgAccountIds.value
    )
    if (res.err_code === 0) {
      ElMessage.success('配置成功')
      showTgAccountDialog.value = false
      await loadDepartments() // 重新加载以更新关联数量
    } else {
      ElMessage.error(res.err_msg || '配置失败')
    }
  } catch (error: any) {
    ElMessage.error('配置失败: ' + (error.message || '未知错误'))
  } finally {
    submitting.value = false
  }
}

// 重置表单
const resetForm = () => {
  isEditing.value = false
  departmentForm.value = {
    id: 0,
    name: '',
    description: '',
    is_active: 1
  }
  departmentFormRef.value?.resetFields()
}

// 组件挂载时加载数据
onMounted(() => {
  loadDepartments()
})
</script>

<style scoped>
.department-manage {
  height: 100%;
}

.table-card {
  width: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

:deep(.el-transfer) {
  display: flex;
  align-items: center;
  justify-content: center;
}

:deep(.el-transfer-panel) {
  width: 280px;
}

:deep(.el-transfer__buttons) {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 0 20px;
  gap: 12px;
}

:deep(.el-transfer__button) {
  display: block;
  margin: 0;
}
</style>
