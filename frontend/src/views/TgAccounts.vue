<template>
  <div class="tg-accounts">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>Telegram账户管理</span>
          <el-button type="primary" @click="showAddDialog = true">
            <el-icon><Plus /></el-icon>
            添加账户
          </el-button>
        </div>
      </template>

      <!-- 账户列表表格 -->
      <el-table :data="accounts" style="width: 100%" v-loading="loading">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="name" label="连接名称" width="120" />
        <el-table-column prop="phone" label="手机号" width="150" />
        <el-table-column prop="nickname" label="昵称" width="150" />
        <el-table-column prop="user_id" label="数字ID" width="120" />
        <el-table-column prop="username" label="用户名" width="150" />
        <el-table-column label="群组数量" width="100" align="center">
          <template #default="scope">
            <span>{{ scope.row.group_count || 0 }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="creator_username" label="创建者" width="120" />
        <el-table-column prop="status_text" label="状态" width="100">
          <template #default="scope">
            <el-tag
              :type="getStatusType(scope.row.status)"
              size="small"
            >
              {{ scope.row.status_text }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="scope">
            {{ formatUTCToLocal(scope.row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" fixed="right" width="300">
          <template #default="scope">
            <el-button
              size="small"
              @click="handleLogin(scope.row)"
              :disabled="scope.row.status === 1"
              :type="scope.row.status === 1 ? 'success' : 'primary'"
            >
              {{ scope.row.status === 1 ? '已登录' : '登录' }}
            </el-button>
            <el-button
              size="small"
              type="info"
              @click="handleViewStatus(scope.row)"
            >
              状态
            </el-button>
            <el-button
              size="small"
              type="warning"
              @click="handleSearchHistory(scope.row)"
              :disabled="scope.row.status !== 1"
            >
              获取群组
            </el-button>
            <el-popconfirm
              title="确定删除此账户吗？"
              @confirm="handleDelete(scope.row)"
            >
              <template #reference>
                <el-button size="small" type="danger">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 添加账户对话框 -->
    <el-dialog v-model="showAddDialog" title="添加Telegram账户" width="500px">
      <el-form :model="addForm" :rules="addRules" ref="addFormRef" label-width="100px">
        <el-form-item label="连接名称" prop="name">
          <el-input v-model="addForm.name" />
          <div class="form-help-text">用于系统识别电报账户，仅可包含字母或数字</div>
        </el-form-item>
        <el-form-item label="手机号" prop="phone">
          <el-input v-model="addForm.phone" />
          <div class="form-help-text">输入带国际区号的手机号，例如+11234567890</div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="handleAdd" :loading="adding">确定</el-button>
      </template>
    </el-dialog>

    <!-- 登录流程对话框 -->
    <el-dialog v-model="showLoginDialog" title="Telegram账户登录" width="500px" :close-on-click-modal="false">
      <div v-if="loginStep === 1">
        <el-result icon="info" title="发送验证码" sub-title="系统将向您的手机号发送验证码">
          <template #extra>
            <el-text type="info" size="small">
              验证码将通过Telegram应用或短信发送到您的手机
            </el-text>
          </template>
        </el-result>
      </div>
      
      <div v-if="loginStep === 2">
        <el-result icon="info" title="验证码已发送" sub-title="请检查您的Telegram应用或短信">
          <template #extra>
            <el-form :model="loginForm" label-width="100px">
              <el-form-item label="验证码">
                <el-input v-model="loginForm.code" placeholder="请输入6位验证码" maxlength="6" />
              </el-form-item>
            </el-form>
          </template>
        </el-result>
      </div>

      <div v-if="loginStep === 3">
        <el-result icon="warning" title="需要二次验证" sub-title="请输入您的2FA密码">
          <template #extra>
            <el-form :model="loginForm" label-width="100px">
              <el-form-item label="2FA密码">
                <el-input v-model="loginForm.password" type="password" placeholder="请输入2FA密码" />
              </el-form-item>
            </el-form>
          </template>
        </el-result>
      </div>

      <template #footer>
        <el-button @click="handleCancelLogin">取消</el-button>
        <el-button type="primary" @click="handleLoginNext" :loading="loginLoading">
          {{ getLoginButtonText() }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 账户状态对话框 -->
    <el-dialog v-model="showStatusDialog" title="账户状态" width="800px">
      <div v-if="currentAccountStatus">
        <el-descriptions border :column="1" class="status-info">
          <el-descriptions-item label="ID">{{ currentAccountStatus.id }}</el-descriptions-item>
          <el-descriptions-item label="手机号">{{ currentAccountStatus.phone }}</el-descriptions-item>
          <el-descriptions-item label="用户ID">{{ currentAccountStatus.user_id }}</el-descriptions-item>
          <el-descriptions-item label="用户名">{{ currentAccountStatus.username }}</el-descriptions-item>
          <el-descriptions-item label="昵称">{{ currentAccountStatus.nickname }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusType(currentAccountStatus.status)">
              {{ currentAccountStatus.status_text }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="2FA" v-if="currentAccountStatus.two_step">
            <el-tag type="warning">已启用</el-tag>
          </el-descriptions-item>
        </el-descriptions>
        
        <!-- 关联群组信息 -->
        <div class="groups-section">
          <h3>关联群组</h3>
          <el-table 
            :data="accountGroups" 
            v-loading="groupsLoading" 
            style="width: 100%" 
            :height="200"
            empty-text="暂无关联群组"
          >
            <el-table-column prop="title" label="群组名称" min-width="200" show-overflow-tooltip />
            <el-table-column prop="group_type" label="类型" width="80">
              <template #default="scope">
                <el-tag :type="scope.row.group_type === 1 ? 'info' : 'primary'" size="small">
                  {{ scope.row.group_type_text || '群组' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="80">
              <template #default="scope">
                <el-tag :type="scope.row.status === 1 ? 'success' : 'warning'" size="small">
                  {{ scope.row.status_text || '未知' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="加入时间" width="160" show-overflow-tooltip>
              <template #default="scope">
                {{ formatUTCToLocal(scope.row.created_at) }}
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import {
  getTgAccountList,
  addTgAccount,
  sendPhoneCode,
  verifyCode,
  updatePassword,
  deleteAccount,
  getAccountStatus,
  fetchAccountGroupInfo,
  getAccountGroups
} from '@/api/tg-accounts'
import type { TgAccount, TgAccountStatusResponse, TgAccountGroup } from '@/api/tg-accounts'
import { formatUTCToLocal } from '@/utils/date'

// 响应式数据
const accounts = ref<TgAccount[]>([])
const loading = ref(false)
const showAddDialog = ref(false)
const showLoginDialog = ref(false)
const showStatusDialog = ref(false)
const adding = ref(false)
const loginLoading = ref(false)
const loginStep = ref(1) // 1: API凭证, 2: 验证码, 3: 2FA密码
const currentAccount = ref<TgAccount | null>(null)
const currentAccountStatus = ref<TgAccountStatusResponse | null>(null)
const accountGroups = ref<TgAccountGroup[]>([])
const groupsLoading = ref(false)

// 表单数据
const addForm = reactive({
  name: '',
  phone: ''
})

const loginForm = reactive({
  api_id: '',
  api_hash: '',
  code: '',
  password: ''
})

// 表单验证规则
const addRules = {
  name: [
    { required: true, message: '请输入连接名称', trigger: 'blur' },
    { pattern: /^[a-zA-Z0-9]+$/, message: '连接名称只能包含字母和数字', trigger: 'blur' }
  ],
  phone: [
    { required: true, message: '请输入手机号', trigger: 'blur' }
  ]
}

const addFormRef = ref()

// 获取状态标签类型
const getStatusType = (status: number) => {
  switch (status) {
    case 0: return 'info'    // 未登录
    case 1: return 'success' // 登录成功
    case 2: return 'danger'  // 登录失败
    case 3: return 'warning' // 登录中
    default: return 'info'
  }
}

// 获取登录按钮文本
const getLoginButtonText = () => {
  switch (loginStep.value) {
    case 1: return '发送验证码'
    case 2: return '验证登录'
    case 3: return '完成登录'
    default: return '下一步'
  }
}

// 加载账户列表
const loadAccounts = async () => {
  loading.value = true
  try {
    const response = await getTgAccountList()
    if (response.err_code === 0) {
      accounts.value = Array.isArray(response.payload) ? response.payload : []
    } else {
      ElMessage.error(response.err_msg || '加载账户列表失败')
    }
  } catch (error: any) {
    console.error('加载账户列表详细错误:', error)
    console.error('错误响应数据:', error.response?.data)
    console.error('错误状态码:', error.response?.status)
    console.error('请求URL:', error.config?.url)
    
    // 如果是401错误，显示需要登录的提示
    if (error.response?.status === 401) {
      ElMessage.warning('请先登录后再访问此页面')
    } else if (error.response?.status === 404) {
      ElMessage.error('API接口不存在，请检查服务器配置')
    } else if (error.response?.status === 400) {
      const errorMsg = error.response?.data?.err_msg || '请求参数错误'
      ElMessage.error('加载账户列表失败: ' + errorMsg)
    } else {
      ElMessage.error('加载账户列表失败: ' + (error.message || '网络错误'))
    }
    console.error('Load accounts error:', error)
  } finally {
    loading.value = false
  }
}

// 添加账户
const handleAdd = async () => {
  if (!addFormRef.value) return
  
  await addFormRef.value.validate(async (valid: boolean) => {
    if (!valid) return
    
    adding.value = true
    try {
      const response = await addTgAccount(addForm)
      if (response.err_code === 0) {
        ElMessage.success('账户添加成功')
        showAddDialog.value = false
        addForm.name = ''
        addForm.phone = ''
        loadAccounts()
      } else {
        ElMessage.error(response.err_msg || '添加账户失败')
      }
    } catch (error: any) {
      ElMessage.error('添加账户失败')
      console.error(error)
    } finally {
      adding.value = false
    }
  })
}

// 开始登录流程
const handleLogin = (account: TgAccount) => {
  currentAccount.value = account
  loginStep.value = 1
  loginForm.code = ''
  loginForm.password = ''
  showLoginDialog.value = true
}

// 登录下一步
const handleLoginNext = async () => {
  if (!currentAccount.value) return

  loginLoading.value = true
  try {
    if (loginStep.value === 1) {
      // 先确保账户存在，如果不存在则先添加
      try {
        await addTgAccount({
          name: currentAccount.value.name,
          phone: currentAccount.value.phone
        })
      } catch (error) {
        // 如果账户已存在，忽略错误继续发送验证码
        console.log('账户可能已存在，继续发送验证码')
      }
      
      // 发送验证码，使用系统配置的API凭证
      await sendPhoneCode({ phone: currentAccount.value.phone })
      loginStep.value = 2
      ElMessage.success('验证码已发送')

    } else if (loginStep.value === 2) {
      // 验证验证码
      if (!loginForm.code) {
        ElMessage.warning('请输入验证码')
        return
      }

      try {
        const response = await verifyCode({
          phone: currentAccount.value.phone,
          code: loginForm.code
        })

        if (response.err_code === 0) {
          if (response.payload.needs_2fa) {
            // 需要2FA
            loginStep.value = 3
            ElMessage.info('需要输入2FA密码')
          } else {
            // 登录成功
            ElMessage.success('登录成功')
            showLoginDialog.value = false
            loadAccounts()
          }
        } else {
          ElMessage.error(response.err_msg || '验证失败')
        }
      } catch (error: any) {
        ElMessage.error('验证失败: ' + (error.response?.data?.err_msg || error.message))
      }

    } else if (loginStep.value === 3) {
      // 输入2FA密码
      if (!loginForm.password) {
        ElMessage.warning('请输入2FA密码')
        return
      }

      try {
        const response = await updatePassword({
          phone: currentAccount.value.phone,
          password: loginForm.password
        })

        if (response.err_code === 0) {
          ElMessage.success('登录成功')
          showLoginDialog.value = false
          loadAccounts()
        } else {
          ElMessage.error(response.err_msg || '2FA验证失败')
        }
      } catch (error: any) {
        ElMessage.error('2FA验证失败: ' + (error.response?.data?.err_msg || error.message))
      }
    }
  } catch (error: any) {
    console.error('详细错误信息:', error)
    console.error('错误响应数据:', error.response?.data)
    console.error('错误状态码:', error.response?.status)
    console.error('请求URL:', error.config?.url)
    console.error('请求方法:', error.config?.method)
    console.error('请求数据:', error.config?.data)
    
    const errorMsg = error.response?.data?.err_msg || error.message || '操作失败'
    ElMessage.error('操作失败: ' + errorMsg)
  } finally {
    loginLoading.value = false
  }
}

// 取消登录
const handleCancelLogin = () => {
  showLoginDialog.value = false
  loginStep.value = 1
  currentAccount.value = null
}

// 查看账户状态
const handleViewStatus = async (account: TgAccount) => {
  try {
    // 获取账户状态
    const statusResponse = await getAccountStatus(account.id)
    if (statusResponse.err_code === 0) {
      currentAccountStatus.value = statusResponse.payload
      
      // 同时获取账户的群组信息
      groupsLoading.value = true
      try {
        const groupsResponse = await getAccountGroups(account.id)
        if (groupsResponse.err_code === 0) {
          // 检查payload的结构，可能数据在groups属性中
          if (Array.isArray(groupsResponse.payload)) {
            accountGroups.value = groupsResponse.payload
          } else if (groupsResponse.payload && Array.isArray(groupsResponse.payload.groups)) {
            accountGroups.value = groupsResponse.payload.groups
          } else if (groupsResponse.payload && Array.isArray(groupsResponse.payload.data)) {
            accountGroups.value = groupsResponse.payload.data
          } else {
            accountGroups.value = []
            console.warn('无法解析群组数据结构:', groupsResponse.payload)
          }
        } else {
          accountGroups.value = []
          console.warn('获取群组信息失败:', groupsResponse.err_msg)
        }
      } catch (groupError: any) {
        accountGroups.value = []
        console.warn('获取群组信息失败:', groupError)
      } finally {
        groupsLoading.value = false
      }
      
      showStatusDialog.value = true
    } else {
      ElMessage.error(statusResponse.err_msg || '获取状态失败')
    }
  } catch (error: any) {
    ElMessage.error('获取状态失败')
    console.error(error)
  }
}

// 搜索聊天记录
const handleSearchHistory = async (account: TgAccount) => {
  try {
    await ElMessageBox.confirm(
      '确定要获取此账户的群组信息吗？系统将获取所有群聊和频道信息，并建立会话关系。这可能需要一些时间。',
      '确认获取群组信息',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    const response = await fetchAccountGroupInfo(account.id)
    if (response.err_code === 0) {
      ElMessage.success(`已开始获取账户 ${account.name} 的群组信息，任务ID: ${response.payload.task_id}`)
    } else {
      ElMessage.error(response.err_msg || '获取群组信息失败')
    }
  } catch (error: any) {
    if (error === 'cancel') {
      console.log('用户取消操作')
    } else {
      ElMessage.error('获取群组信息失败: ' + (error.response?.data?.err_msg || error.message))
      console.error('Fetch group info error:', error)
    }
  }
}

// 删除账户
const handleDelete = async (account: TgAccount) => {
  try {
    console.log('开始删除账户:', account.id)
    const response = await deleteAccount(account.id)
    console.log('删除API响应:', response)
    if (response.err_code === 0) {
      ElMessage.success('删除成功')
      loadAccounts()
    } else {
      ElMessage.error(response.err_msg || '删除失败')
    }
  } catch (error: any) {
    console.error('删除失败，详细错误:', error)
    ElMessage.error('删除失败: ' + (error.response?.data?.err_msg || error.message))
  }
}

// 组件挂载时加载数据
onMounted(() => {
  loadAccounts()
})
</script>

<style scoped>
.tg-accounts {
  height: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.el-table {
  margin-top: 20px;
}

.form-help-text {
  color: #909399;
  font-size: 12px;
  line-height: 1.4;
  margin-top: 4px;
}

.status-info {
  margin-bottom: 20px;
}

.groups-section h3 {
  margin: 0 0 15px 0;
  color: #303133;
  font-size: 16px;
  font-weight: 600;
}
</style>