<template>
  <div class="user-manage">
    <!-- 选项卡布局 -->
    <el-tabs v-model="activeTab" type="card">
      <!-- 用户列表选项卡 -->
      <el-tab-pane label="用户列表" name="users">
        <el-card class="table-card">
          <template #header>
            <div class="card-header">
              <span>用户列表</span>
              <el-button type="primary" @click="showCreateDialog = true">
                <el-icon><Plus /></el-icon>
                新增用户
              </el-button>
            </div>
          </template>

          <el-table :data="users" style="width: 100%" v-loading="loading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column label="用户名" width="150">
          <template #default="scope">
            <span :style="{ color: scope.row.status === 0 ? '#909399' : '' }">
              {{ scope.row.username }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="permission_name" label="角色" width="140">
          <template #default="scope">
            <el-tag
              :type="getPermissionTagType(scope.row.permission_level)"
              size="small"
            >
              {{ scope.row.permission_name }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="department_name" label="所属部门" width="150">
          <template #default="scope">
            <span>{{ scope.row.department_name || '未分配' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="scope">
            <el-tag 
              :type="scope.row.status === 1 ? 'success' : 'danger'" 
              size="small"
            >
              {{ scope.row.status === 1 ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="last_login" label="最后登录" width="160" />
        <el-table-column prop="created_at" label="创建时间" width="160" />
        <el-table-column label="操作" width="340" fixed="right">
          <template #default="scope">
            <div class="action-buttons">
              <el-button
                type="primary"
                size="small"
                @click="editUser(scope.row)"
              >
                编辑
              </el-button>
              <el-button
                type="warning"
                size="small"
                @click="handleResetPassword(scope.row.id)"
              >
                重置密码
              </el-button>
              <el-button
                v-if="scope.row.status === 1"
                type="danger"
                size="small"
                @click="handleDisableUser(scope.row.id)"
              >
                禁用
              </el-button>
              <el-button
                v-else
                type="success"
                size="small"
                @click="handleEnableUser(scope.row)"
              >
                启用
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
        </el-card>
      </el-tab-pane>

      <!-- 部门管理选项卡（仅超级管理员可见） -->
      <el-tab-pane label="部门管理" name="departments" v-if="isSuperAdmin">
        <DepartmentManage />
      </el-tab-pane>
    </el-tabs>

    <!-- 新增用户对话框 -->
    <el-dialog v-model="showCreateDialog" title="新增安全用户" width="500px">
      <el-form :model="createForm" label-width="100px" :rules="createRules" ref="createFormRef">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="createForm.username" placeholder="请输入用户名（至少3位）" />
        </el-form-item>
        <el-form-item label="初始密码" prop="password">
          <el-input 
            v-model="createForm.password" 
            placeholder="留空使用默认密码 123456"
            show-password
          />
        </el-form-item>
        <el-form-item label="角色" prop="permission_level">
          <el-select v-model="createForm.permission_level" placeholder="请选择角色" style="width: 100%">
            <el-option
              v-for="level in permissionLevels"
              :key="level.id"
              :label="level.name"
              :value="level.id"
            >
              <div style="display: flex; justify-content: space-between; align-items: center;">
                <span>{{ level.name }}</span>
                <el-tag
                  :type="getPermissionTagType(level.id)"
                  size="small"
                >
                  {{ level.id === 0 ? '超管' : level.id === 1 ? '部门管理员' : '普通用户' }}
                </el-tag>
              </div>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="所属部门" prop="department_id">
          <el-select v-model="createForm.department_id" placeholder="请选择部门" style="width: 100%">
            <el-option
              v-for="dept in departments"
              :key="dept.id"
              :label="dept.name"
              :value="dept.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showCreateDialog = false">取消</el-button>
          <el-button type="primary" @click="createUserHandler" :loading="createLoading">
            确定
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 编辑用户对话框 -->
    <el-dialog v-model="showEditDialog" title="编辑安全用户" width="500px">
      <el-form :model="editForm" label-width="100px" ref="editFormRef">
        <el-form-item label="用户名">
          <el-input v-model="editForm.username" disabled />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="editForm.permission_level" placeholder="请选择角色" style="width: 100%">
            <el-option
              v-for="level in permissionLevels"
              :key="level.id"
              :label="level.name"
              :value="level.id"
            >
              <div style="display: flex; justify-content: space-between; align-items: center;">
                <span>{{ level.name }}</span>
                <el-tag
                  :type="getPermissionTagType(level.id)"
                  size="small"
                >
                  {{ level.id === 0 ? '超管' : level.id === 1 ? '部门管理员' : '普通用户' }}
                </el-tag>
              </div>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="所属部门">
          <el-select v-model="editForm.department_id" placeholder="请选择部门" style="width: 100%">
            <el-option
              v-for="dept in departments"
              :key="dept.id"
              :label="dept.name"
              :value="dept.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-radio-group v-model="editForm.status">
            <el-radio :label="1">启用</el-radio>
            <el-radio :label="0">禁用</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showEditDialog = false">取消</el-button>
          <el-button type="primary" @click="updateUserHandler" :loading="updateLoading">
            确定
          </el-button>
        </div>
      </template>
    </el-dialog>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, InfoFilled } from '@element-plus/icons-vue'
import {
  getSecureUserList,
  createSecureUser,
  updateSecureUser,
  deleteSecureUser,
  resetUserPassword,
  getSecureUserInfo
} from '@/api/user'
import type { SecureUser, PermissionLevel } from '@/api/user'
import { useDepartmentStore } from '@/store/department'
import DepartmentManage from './DepartmentManage.vue'

// Store
const departmentStore = useDepartmentStore()

// 响应式数据
const users = ref<SecureUser[]>([])
const permissionLevels = ref<PermissionLevel[]>([])
const loading = ref(false)
const activeTab = ref('users')
const currentUser = ref<SecureUser | null>(null)

// 计算属性
const departments = computed(() => departmentStore.departments)
const isSuperAdmin = computed(() => currentUser.value?.permission_level === 0)

// 对话框状态
const showCreateDialog = ref(false)
const showEditDialog = ref(false)

// 表单数据
const createLoading = ref(false)
const updateLoading = ref(false)
const createFormRef = ref()
const editFormRef = ref()

const createForm = ref({
  username: '',
  password: '',
  permission_level: 2,
  department_id: 0
})

const editForm = ref({
  id: 0,
  username: '',
  permission_level: 2,
  department_id: 0,
  status: 1
})

// 表单验证规则
const createRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, message: '用户名长度不能少于3位', trigger: 'blur' }
  ],
  permission_level: [
    { required: true, message: '请选择角色', trigger: 'change' }
  ]
}

// 权限等级工具函数
const getPermissionTagType = (permissionLevel: number): string => {
  switch (permissionLevel) {
    case 0:
      return 'danger'  // 红色 - 超级管理员
    case 1:
      return 'warning' // 橙色 - 部门管理员
    case 2:
      return 'success' // 绿色 - 普通用户
    default:
      return 'info'    // 灰色 - 未知
  }
}

// 获取当前用户信息
const fetchCurrentUser = async () => {
  try {
    const response = await getSecureUserInfo()
    if (response.err_code === 0) {
      currentUser.value = response.payload as SecureUser
    }
  } catch (error) {
    console.error('获取当前用户信息失败', error)
  }
}

// 获取用户列表
const fetchUsers = async () => {
  try {
    loading.value = true
    const response = await getSecureUserList()
    if (response.err_code === 0) {
      users.value = response.payload.users
      permissionLevels.value = response.payload.roles
    } else {
      ElMessage.error(response.err_msg || '获取用户列表失败')
    }
  } catch (error) {
    ElMessage.error('获取用户列表失败')
  } finally {
    loading.value = false
  }
}

// 新增用户
const createUserHandler = async () => {
  if (!createFormRef.value) return
  
  try {
    await createFormRef.value.validate()
    createLoading.value = true
    
    const response = await createSecureUser(createForm.value)
    if (response.err_code === 0) {
      ElMessage.success(`用户创建成功！默认密码：${response.payload.default_password}`)
      showCreateDialog.value = false
      createForm.value = { username: '', password: '', permission_level: 2 }
      await fetchUsers()
    } else {
      ElMessage.error(response.err_msg || '创建用户失败')
    }
  } catch (error) {
    ElMessage.error('创建用户失败')
  } finally {
    createLoading.value = false
  }
}

// 编辑用户
const editUser = (user: SecureUser) => {
  editForm.value = {
    id: user.id,
    username: user.username,
    permission_level: user.permission_level,
    department_id: (user as any).department_id || 0,
    status: user.status
  }
  showEditDialog.value = true
}

// 更新用户
const updateUserHandler = async () => {
  try {
    updateLoading.value = true
    const response = await updateSecureUser({
      user_id: editForm.value.id,
      permission_level: editForm.value.permission_level,
      status: editForm.value.status
    })
    
    if (response.err_code === 0) {
      ElMessage.success('用户更新成功')
      showEditDialog.value = false
      await fetchUsers()
    } else {
      ElMessage.error(response.err_msg || '更新用户失败')
    }
  } catch (error) {
    ElMessage.error('更新用户失败')
  } finally {
    updateLoading.value = false
  }
}


// 重置密码
const handleResetPassword = async (userId: number) => {
  try {
    await ElMessageBox.confirm('确定要重置该用户的密码吗？', '重置密码', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })

    const response = await resetUserPassword(userId)
    if (response.err_code === 0) {
      ElMessage.success(`密码重置成功！新密码：${response.payload.new_password}`)
      await fetchUsers()
    } else {
      ElMessage.error(response.err_msg || '重置密码失败')
    }
  } catch (error) {
    // 用户取消操作
  }
}

// 禁用用户
const handleDisableUser = async (userId: number) => {
  try {
    await ElMessageBox.confirm('确定要禁用该用户吗？', '禁用用户', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })

    const response = await deleteSecureUser(userId)
    if (response.err_code === 0) {
      ElMessage.success('用户已禁用')
      await fetchUsers()
    } else {
      ElMessage.error(response.err_msg || '禁用用户失败')
    }
  } catch (error) {
    // 用户取消操作
  }
}

// 启用用户
const handleEnableUser = async (user: SecureUser) => {
  try {
    await ElMessageBox.confirm('确定要启用该用户吗？', '启用用户', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'info',
    })

    const response = await updateSecureUser({
      user_id: user.id,
      permission_level: user.permission_level,
      status: 1  // 启用
    })

    if (response.err_code === 0) {
      ElMessage.success('用户已启用')
      await fetchUsers()
    } else {
      ElMessage.error(response.err_msg || '启用用户失败')
    }
  } catch (error) {
    // 用户取消操作
  }
}

// 页面加载时获取数据
onMounted(async () => {
  await fetchCurrentUser()
  await departmentStore.fetchDepartments()
  await fetchUsers()
})
</script>

<style scoped>
.user-manage {
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

.action-buttons {
  display: flex;
  gap: 8px;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.status-column {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.error-attempts {
  color: #f56c6c;
  font-weight: bold;
}

.dialog-footer {
  text-align: right;
}

.comparison-content h4 {
  margin-bottom: 10px;
  color: #303133;
}

.feature-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.feature-item {
  padding: 4px 0;
  line-height: 1.5;
}

.feature-item.good {
  color: #67c23a;
}

.feature-item.bad {
  color: #f56c6c;
}

.feature-item.neutral {
  color: #909399;
}

.migration-info {
  background-color: #f4f4f5;
  padding: 15px;
  border-radius: 6px;
}

.migration-info h4 {
  margin-top: 0;
  margin-bottom: 10px;
}

.migration-info p {
  margin: 5px 0;
  line-height: 1.6;
}

.migration-info code {
  background-color: #e4e7ed;
  padding: 2px 4px;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
}
</style>